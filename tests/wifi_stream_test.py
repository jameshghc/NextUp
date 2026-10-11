"""Streaming from the PC over home Wi-Fi: play tickets on the PC's phone
link, pairing over the cable, the phone finding the PC, history both ways,
and the phone playing a stream. Against a sandbox copy of everything (see
devserve.isolate), on port 8797, with no network beyond this machine."""
import sys, os, re, json, time, tempfile
sys.path.insert(0, r"X:\NextUp"); os.chdir(r"X:\NextUp"); sys.argv = ["nextup.py"]
import nextup as n
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from devserve import isolate
HOME = os.path.join(tempfile.gettempdir(), "nextup_wifistream")
isolate(n, HOME)
WORK = os.path.join(HOME, "media")
os.makedirs(WORK, exist_ok=True)

results = []
def check(name, ok, detail=""):
    ok = bool(ok); results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- %s" % (detail,)) if detail != "" else ""))

import urllib.request, urllib.error
PORT = 8797
BASE = "http://127.0.0.1:%d" % PORT
PHONE = "0123456789abcdef"

def call(method, path, token=None, body=None, headers=None):
    """(status, headers, bytes), errors returned rather than raised."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    if token:
        req.add_header("Authorization", "Bearer " + token)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.headers, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()

def jcall(*a, **k):
    st, h, body = call(*a, **k)
    try:
        return st, json.loads(body)
    except ValueError:
        return st, {}

def pair():
    code = n.phone_pair_start()["code"]
    return n.phone_pair_finish(code, PHONE, "S24 Ultra")

# --- the library on the PC ---------------------------------------------------------
NAME = "Don\u2019t Look Up \u2013 2021"
film = os.path.join(WORK, NAME + ".mkv")
data = bytes(range(256)) * 1171 + bytes(range(224))      # 300 000 bytes
assert len(data) == 300000
open(film, "wb").write(data)
open(os.path.join(WORK, NAME + ".en.srt"), "w", encoding="utf-8").write("1\n00:00:01,000 --> 00:00:02,000\nhi\n")
open(os.path.join(WORK, NAME + ".forced.ass"), "w", encoding="utf-8").write("[Script Info]\n")
open(os.path.join(WORK, "Something Else.srt"), "w").write("not ours")
other = os.path.join(WORK, "Other Film.mkv")
open(other, "wb").write(b"B" * 5000)
conn = n.db()
cur = conn.execute("INSERT INTO movies (path,title,year,tmdb_id) VALUES (?,?,?,?)",
                   (film, "Don't Look Up", 2021, "777001"))
film_id = cur.lastrowid
conn.execute("INSERT INTO movies (path,title,year,tmdb_id) VALUES (?,?,?,?)",
             (other, "Other Film", 2020, "777002"))
cur = conn.execute("INSERT INTO shows (name,title,tmdb_id) VALUES (?,?,?)",
                   ("wifi show", "Wifi Show", "777003"))
show_id = cur.lastrowid
ep = os.path.join(WORK, "Wifi Show S01E01.mkv")
open(ep, "wb").write(b"E" * 4000)
conn.execute("INSERT INTO episodes (path,show_id,season,episode) VALUES (?,?,?,?)",
             (ep, show_id, 1, 1))
conn.commit(); conn.close()

n.phone_link_start(PORT, "127.0.0.1")
token = pair()

# --- Task 1: play tickets ------------------------------------------------------------
st, _ = jcall("POST", "/phone/play", body={"key": "m777001"})
check("play needs a token", st == 401, st)
st, play = jcall("POST", "/phone/play", token, body={"key": "m777001"})
check("play gives a ticket", st == 200 and re.fullmatch(r"/phone/stream/[A-Za-z0-9_-]{32}", play.get("url") or "")
      and len(play.get("subs") or []) == 2 and play.get("resume") == 0, (st, play))
check("the title is the file's name", play.get("title") == NAME, play.get("title"))
conn = n.db(); conn.execute("UPDATE movies SET resume_pos=1234, resume_total=6000 WHERE id=?", (film_id,)); conn.commit(); conn.close()
st, again = jcall("POST", "/phone/play", token, body={"key": "m777001"})
check("resume comes from the PC", again.get("resume") == 1234, again)
check("unknown key 404", jcall("POST", "/phone/play", token, body={"key": "m1"})[0] == 404)
check("episode not on the PC 404", jcall("POST", "/phone/play", token, body={"key": "e777003s1e9"})[0] == 404)
real_check = n.media_file_check
n.media_file_check = lambda p: None
st, body = jcall("POST", "/phone/play", token, body={"key": "m777001"})
n.media_file_check = real_check
check("sleeping drive 503", st == 503, (st, body))

url = play.get("url") or "/phone/stream/x"
st, h, body = call("GET", url)
check("stream whole, no token needed", st == 200 and body == data, (st, len(body)))
check("stream is inline, named the RFC 5987 way",
      (h.get("Content-Disposition") or "").startswith("inline")
      and "filename*=UTF-8''" in (h.get("Content-Disposition") or ""), h.get("Content-Disposition"))
check("stream says it's a video", h.get("Content-Type") == "video/x-matroska", h.get("Content-Type"))
st, h, body = call("GET", url, headers={"Range": "bytes=299999-"})
check("range at the very end", st == 206 and body == data[-1:] and h.get("Content-Range") == "bytes 299999-299999/300000",
      (st, h.get("Content-Range")))
st, h, _b = call("GET", url, headers={"Range": "bytes=300000-"})
check("range past the end 416", st == 416 and h.get("Content-Range") == "bytes */300000", st)
st, _h, body = call("GET", url + "/sub/0")
st9 = call("GET", url + "/sub/9")[0]
check("sub 0 served, sub 9 404", st == 200 and b"hi" in body and st9 == 404, (st, st9))
check("bad ticket 404", call("GET", "/phone/stream/" + "A" * 32)[0] == 404)
st, _h, body = call("GET", url + "?key=m777002")
st2 = call("GET", url + "/../m777002")[0]
check("a ticket names one file", body == data and b"BBBB" not in body and st2 == 404, (st, st2))

st, hello = jcall("GET", "/phone/hello", token)
check("hello says device_id", hello.get("device_id") == n.sync_device_id(), hello)

n.phone_forget(PHONE)
check("forget drops tickets", call("GET", url)[0] == 404)
token = pair()
url = jcall("POST", "/phone/play", token, body={"key": "m777001"})[1].get("url")
n.phone_link_set(False)
n.phone_link_start(PORT, "127.0.0.1")
check("link off drops tickets", call("GET", url)[0] == 404)
url = jcall("POST", "/phone/play", token, body={"key": "m777001"})[1].get("url")
t = url.rsplit("/", 1)[1]
n._PHONE_TICKETS[t][2] = time.time() - 43201
check("tickets expire after 12 idle hours", call("GET", url)[0] == 404)
first = jcall("POST", "/phone/play", token, body={"key": "m777001"})[1].get("url")
for _ in range(20):
    last = jcall("POST", "/phone/play", token, body={"key": "m777001"})[1].get("url")
check("twenty live tickets per phone", call("GET", first)[0] == 404 and call("GET", last)[0] == 200)

# The rest of the suite (tasks 2 to 5) appends below this line.

# --- Task 2: pairing over the cable -------------------------------------------------
direct = n.phone_pair_direct(PHONE, "S24 Ultra")
check("direct pairing gives a working token", call("GET", "/phone/hello", direct)[0] == 200)
def refused(fn, *a):
    try:
        fn(*a)
    except n.AppError:
        return True
    return False
check("direct pairing refuses a bad id", refused(n.phone_pair_direct, "../etc", "x"))
check("direct pairing refuses this PC's own id", refused(n.phone_pair_direct, n.sync_device_id(), "x"))
again = n.phone_pair_direct(PHONE, "S24 Ultra")
check("re-pairing replaces the old token", call("GET", "/phone/hello", direct)[0] == 401
      and call("GET", "/phone/hello", again)[0] == 200)
token = again
n.phone_link_stop()
print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
