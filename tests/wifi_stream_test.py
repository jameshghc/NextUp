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

import urllib.request, urllib.error, threading
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
# --- Task 3: the phone finds the PC ---------------------------------------------------
# This process now plays the phone too: same library, but it looks for the
# PC's link on loopback, where the PC half above is listening.
n.PLATFORM = "android"
def link_cfg(addresses):
    n.CONFIG["pc_link"] = {"token": token, "pc": "Test PC", "pc_id": n.sync_device_id(),
                           "port": PORT, "addresses": addresses, "last_ip": None}
link_cfg(["127.0.0.1"])
st = n.pc_link_check(force=True)
check("finds the PC at a stored address", st["up"] and st["pc"] and st["base"] == BASE, st)
link_cfg(["10.255.255.1", "127.0.0.1"])
t0 = time.time()
st = n.pc_link_check(force=True)
check("a dead first address is skipped", st["up"] and n.CONFIG["pc_link"]["last_ip"] == "127.0.0.1",
      (st, n.CONFIG["pc_link"]["last_ip"], round(time.time() - t0, 1)))
link_cfg([])
n.PC_LINK_CALL_TO = "127.0.0.1"
st = n.pc_link_check(force=True)
check("finds it by calling out", st["up"] and n.CONFIG["pc_link"]["last_ip"] == "127.0.0.1", st)
n.phone_forget(PHONE)
st = n.pc_link_check(force=True)
check("forgotten reads as needs pairing", not st["up"] and st["needs_pairing"], st)
token = n.phone_pair_direct(PHONE, "S24 Ultra")
link_cfg(["127.0.0.1"])
check("paired again, it's up", n.pc_link_check(force=True)["up"])
n.phone_link_stop()
t0 = time.time()
st = n.pc_link_check(force=True)
took = time.time() - t0
check("PC off reads as down within 4 s", not st["up"] and took < 4, (st, round(took, 2)))
n.phone_link_start(PORT, "127.0.0.1")
n.pc_link_check(force=True)
asked = []
_real_hello = n._pc_hello
n._pc_hello = lambda *a, **k: asked.append(a) or _real_hello(*a, **k)
n.pc_link_check()
n._pc_hello = _real_hello
check("a recent check is reused", not asked, asked)
# Final review, Important 2: a PC whose dead adapters come first takes
# longer than the page's first look; the status says a check is running so
# the page can look again when it's done.
link_cfg(["10.255.255.1", "10.255.255.2", "127.0.0.1"])
seen = {}
th = threading.Thread(target=lambda: n.pc_link_check(force=True))
th.start(); time.sleep(0.3)
seen["during"] = n.pc_link_public().get("checking")
th.join()
seen["after"] = n.pc_link_public().get("checking")
check("the status says while a check is running", seen == {"during": True, "after": False}, seen)
st, body = n.pc_link_call("GET", "/phone/hello")
check("calls to the PC carry the token", st == 200 and body.get("ok"), (st, body))

desk = n.ThreadingHTTPServer(("127.0.0.1", 8795), n.Handler)
import threading
threading.Thread(target=desk.serve_forever, daemon=True).start()
with urllib.request.urlopen("http://127.0.0.1:8795/api/status", timeout=10) as r:
    status = json.loads(r.read())
check("status carries pc_link", (status.get("pc_link") or {}).get("up") is True
      and status["pc_link"].get("pc"), status.get("pc_link"))
with urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8795/api/link/check",
                                                   data=b"{}", method="POST"), timeout=10) as r:
    checked = json.loads(r.read())
check("the page can ask for a check", "up" in checked, checked)
desk.shutdown()

# --- Task 4: history both ways over Wi-Fi -----------------------------------------------
# A real second machine for the PC: its own process and database. This one
# is the phone from here on, under the phone's own id.
import subprocess
n.CONFIG["device_id"] = PHONE
PC_PORT = 8794
pc = subprocess.Popen([sys.executable, os.path.join(here, "wifi_pc_helper.py"), str(PC_PORT), PHONE],
                      stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
def pc_says(cmd):
    pc.stdin.write(cmd + "\n"); pc.stdin.flush()
    return pc.stdout.readline().strip()
pc_token = pc.stdout.readline().strip()
n.CONFIG["pc_link"] = {"token": pc_token, "pc": "Test PC", "pc_id": "", "port": PC_PORT,
                       "addresses": ["127.0.0.1"], "last_ip": None}
n.pc_link_check(force=True)
n.log_event("movie", film_id, "Don't Look Up", "stopped", seconds=700, position=600, total=6000)
conn = n.db()
uid = conn.execute("SELECT uid FROM history WHERE event='stopped' ORDER BY id DESC LIMIT 1").fetchone()[0]
conn.close()
pc_says("rate 777001 8")
got = n.pc_link_sync()
check("the phone's stop reaches the PC", pc_says("has " + uid) == "1", got)
conn = n.db()
mine = conn.execute("SELECT userrating FROM movies WHERE id=?", (film_id,)).fetchone()[0]
conn.close()
check("the PC's rating reaches the phone", mine == 8, (mine, got))
# Both halves here started as copies of one library, so the first swap moves
# thousands of events and the seeds (what was true before history) shift as
# they land; one more swap carries those. After that it must be still.
n.pc_link_sync()
before = pc_says("inbox")
again = n.pc_link_sync()
check("a second sync adds nothing", again and again.get("from_pc") == 0 and pc_says("inbox") == before,
      (again, before, pc_says("inbox")))
check("the PC's lines are filed under its own id", os.path.exists(
      os.path.join(n.PHONE_SYNC_DIR, "device-%s.jsonl" % n.CONFIG["pc_link"]["pc_id"])),
      n.CONFIG["pc_link"]["pc_id"])
soon = []
_real_soon = n.pc_link_sync_soon
n.pc_link_sync_soon = lambda: soon.append(1)
n.android_play_finished(position=None, duration=None)
n.pc_link_sync_soon = _real_soon
check("every sitting ending swaps history", soon == [1], soon)
pc_says("quit"); pc.wait(10)
n.PC_LINK.update(checked=0)
n.pc_link_check(force=True)
check("link down gives None, no raise", n.pc_link_sync() is None)

# --- Task 5: playing a streamed item -----------------------------------------------------
# The PC (its own process again) has a film and two episodes this phone
# hasn't; the phone's catalogue lists them, greyed.
pc = subprocess.Popen([sys.executable, os.path.join(here, "wifi_pc_helper.py"), str(PC_PORT), PHONE],
                      stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
pc_token = pc.stdout.readline().strip()
pc_says("film 888001 1234")
pc_says("episode 888002 1 1")
pc_says("episode 888002 1 2")
conn = n.db()
conn.execute("DELETE FROM movies WHERE tmdb_id IN ('888001')")
conn.execute("DELETE FROM shows WHERE tmdb_id IN ('888002')")
conn.execute("INSERT OR REPLACE INTO snapshot_movies (tmdb_id,title,year,runtime) VALUES ('888001','PC Only Film',2019,6000)")
conn.execute("INSERT OR REPLACE INTO snapshot_shows (tmdb_id,title,year,episode_count) VALUES ('888002','PC Only Show',2020,3)")
for e in (1, 2, 3):      # the PC's catalogue lists S1E3, but the file isn't there
    conn.execute("INSERT OR REPLACE INTO snapshot_episodes (show_tmdb_id,season,episode,title) VALUES ('888002',1,?,?)",
                 (e, "Episode %d" % e))
conn.commit(); conn.close()
n.CONFIG["pc_link"] = {"token": pc_token, "pc": "Test PC", "pc_id": "", "port": PC_PORT,
                       "addresses": ["127.0.0.1"], "last_ip": None}
n.CONFIG["show_elsewhere"] = True
n.PC_WAKE_PAUSE = 0.05

played = []
n.ANDROID_PLAYER = lambda path, start, subs=None: played.append((path, start, subs))
desk = n.ThreadingHTTPServer(("127.0.0.1", 8795), n.Handler)
threading.Thread(target=desk.serve_forever, daemon=True).start()
def desk_post(path, body):
    req = urllib.request.Request("http://127.0.0.1:8795" + path, data=json.dumps(body).encode(),
                                 method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")
def desk_get(path):
    with urllib.request.urlopen("http://127.0.0.1:8795" + path, timeout=30) as r:
        return json.loads(r.read())

def far(kind):
    return dict((r["tmdb_id"], r) for r in n.elsewhere_rows("all", "") if r["kind"] == kind)
n.PC_LINK.update(up=False, base=None)
down = far("movie").get("888001") or {}
n.pc_link_check(force=True)
up = far("movie").get("888001") or {}
check("elsewhere film marked stream while up, not when down", up.get("stream") and not down.get("stream"),
      (up.get("stream"), down.get("stream")))
check("a show with episodes on the PC is marked too", (far("tvshow").get("888002") or {}).get("stream"))

eps = desk_get("/api/elsewhere/episodes?tmdb_id=888002")
listed = [(e["episode"]) for se in eps.get("seasons", []) for e in se["episodes"]]
check("the show's episodes are listed from the catalogue", eps.get("title") == "PC Only Show"
      and listed == [1, 2, 3] and eps.get("next") == {"season": 1, "episode": 1}, eps)
st, body = desk_post("/api/play", {"stream": {"kind": "episode", "tmdb_id": "888002", "season": 1, "episode": 3}})
check("an episode the PC hasn't got can't be played", body.get("error") and not played, (st, body))

st, body = desk_post("/api/play", {"stream": {"kind": "movie", "tmdb_id": "888001"}, "resume": True})
url, start, subs = played[-1] if played else (None, None, None)
check("stream play hands mpv the PC's address", st == 200 and (url or "").startswith(BASE.replace(str(PORT), str(PC_PORT)) + "/phone/stream/"),
      (st, body, url))
check("start is the PC's point when the phone has none", start == 1234, start)

n._ANDROID_SITTING["started_at"] = time.time() - 900
n.android_play_finished(position=2000, duration=6000)
conn = n.db()
row = conn.execute("SELECT * FROM history WHERE tmdb_id='888001' ORDER BY id DESC LIMIT 1").fetchone()
conn.close()
check("the finish logs a stop on the tmdb identity", row and row["event"] == "stopped" and row["position"] == 2000
      and row["item_id"] is None and row["kind"] == "movie", dict(row) if row else None)
check("elsewhere_progress reads it back", n.elsewhere_progress("movie", "888001") == {"position": 2000, "watched": False},
      n.elsewhere_progress("movie", "888001"))
desk_post("/api/play", {"stream": {"kind": "movie", "tmdb_id": "888001"}, "resume": True})
check("the next play starts at the later point (phone 2000 over PC 1234)", played[-1][1] == 2000, played[-1][1])
desk_post("/api/play", {"stream": {"kind": "movie", "tmdb_id": "888001"}})
check("PLAY without resume starts over", played[-1][1] == 0, played[-1][1])

desk_post("/api/play", {"stream": {"kind": "episode", "tmdb_id": "888002", "season": 1, "episode": 1}})
n._ANDROID_SITTING["started_at"] = time.time() - 1500
n.android_play_finished(completed=True)
eps = desk_get("/api/elsewhere/episodes?tmdb_id=888002")
first = eps["seasons"][0]["episodes"][0]
check("a streamed episode seen to the end is watched", first.get("watched") is True, first)
check("next episode after the last watched", eps.get("next") == {"season": 1, "episode": 2}, eps.get("next"))

# Copied to the phone later: the same film, now a local row with no point of its own.
copy = os.path.join(WORK, "PC Only Film.mkv")
open(copy, "wb").write(b"F" * 1000)
conn = n.db()
cid = conn.execute("INSERT INTO movies (path,title,year,tmdb_id) VALUES (?,?,?,?)",
                   (copy, "PC Only Film", 2019, "888001")).lastrowid
conn.commit(); conn.close()
n.LOCAL.loaded_at = 0
st, body = desk_post("/api/play", {"type": "movie", "id": cid})
check("copied later keeps the point", st == 200 and played[-1][0] == copy and played[-1][1] == 2000,
      (st, body, played[-1]))

# Final review, Important 1: over Wi-Fi a stream can end early (the PC shut
# down, the Wi-Fi dropped) and mpv may close as though it reached the end.
# For a film whose length is known, that only counts as watched if it ran
# for most of it.
conn = n.db(); conn.execute("UPDATE snapshot_movies SET runtime=6000 WHERE tmdb_id='888001'"); conn.commit(); conn.close()
desk_post("/api/play", {"stream": {"kind": "movie", "tmdb_id": "888001"}, "resume": True})
n._ANDROID_SITTING["started_at"] = time.time() - 25 * 60
n.android_play_finished(completed=True)
check("a stream cut short isn't counted as watched", n.elsewhere_progress("movie", "888001")["watched"] is False,
      n.elsewhere_progress("movie", "888001"))
desk_post("/api/play", {"stream": {"kind": "movie", "tmdb_id": "888001"}, "resume": True})
n._ANDROID_SITTING["started_at"] = time.time() - 98 * 60
n.android_play_finished(completed=True)
check("one that ran its length is", n.elsewhere_progress("movie", "888001")["watched"] is True)

# Final review, Important 4: a long show's sheet (and PLAY on its tile) must
# not crawl. 750 episodes and plenty of history.
conn = n.db()
for i in range(750):
    conn.execute("INSERT OR REPLACE INTO snapshot_episodes (show_tmdb_id,season,episode,title) VALUES ('888009',?,?,?)",
                 (1 + i // 25, 1 + i % 25, "E%d" % i))
conn.execute("INSERT OR REPLACE INTO snapshot_shows (tmdb_id,title,year,episode_count) VALUES ('888009','Long Show',1989,750)")
for i in range(0, 750, 3):
    conn.execute("INSERT INTO history (at,kind,item_id,title,event,uid,utc,tmdb_id,season,episode,position)"
                 " VALUES ('2026-01-01 00:00:00','episode',NULL,'x',?,?,?,'888009',?,?,600)",
                 ("watched" if i % 2 else "stopped", "long-%d" % i, 1000.0 + i, 1 + i // 25, 1 + i % 25))
conn.commit(); conn.close()
t0 = time.time()
long_show = n.elsewhere_episodes("888009")
took = time.time() - t0
check("a 750-episode show's sheet is quick", took < 0.5 and sum(len(x["episodes"]) for x in long_show["seasons"]) == 750,
      round(took, 2))

pc_says("asleep 1")
before = len(played)
t0 = time.time()
st, body = desk_post("/api/play", {"stream": {"kind": "movie", "tmdb_id": "888001"}})
check("a sleeping drive is retried, then reported", body.get("error") == "The PC's drive isn't answering"
      and len(played) == before, (st, body, round(time.time() - t0, 2)))
pc_says("asleep 0")
desk.shutdown()
pc_says("quit"); pc.wait(10)

app_src = open(os.path.join("android", "src", "mobile", "app.py"), encoding="utf-8").read()
check("the phone hands mpv a web address as it is, not through the media index",
      'startswith("http")' in app_src and "Uri.parse(path)" in app_src, "")
check("and the subtitles with it", '"subs"' in app_src and '"subs.enable"' in app_src
      and "lambda path, start, subs=None" in app_src, "")

n.phone_link_stop()
print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
