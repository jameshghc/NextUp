"""The phone link, PC side: pairing, the gate, the snapshot, downloads,
sync and being found. Against a sandbox copy of everything (see
devserve.isolate), on ports 8798/8799 so it can run beside the real app,
and with no network beyond this machine."""
import sys, os, re, json, time, tempfile
sys.path.insert(0, r"X:\NextUp"); os.chdir(r"X:\NextUp"); sys.argv = ["nextup.py"]
import nextup as n
here = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(here, "_work")
os.makedirs(WORK, exist_ok=True)
sys.path.insert(0, here)
from devserve import isolate
isolate(n, os.path.join(tempfile.gettempdir(), "nextup_phonelink"))

results = []
def check(name, ok, detail=""):
    ok = bool(ok); results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- %s" % (detail,)) if detail != "" else ""))

def raises(fn, *a):
    try:
        fn(*a)
    except n.AppError as exc:
        return str(exc) or True
    return False

PHONE = "abcdef0123456789"

# --- Task 1: pairing and tokens ------------------------------------------------
code = n.phone_pair_start()["code"]
check("code is four digits", re.fullmatch(r"\d{4}", code), code)
token = n.phone_pair_finish(code, PHONE, "S24 Ultra")
dev = n.phone_device_for_token(token)
check("right code gives a token, stored only as a hash",
      len(token) >= 40 and token not in json.dumps(n.CONFIG) and dev and dev["id"] == PHONE,
      dev)
check("code is single use", raises(n.phone_pair_finish, code, PHONE, "S24 Ultra"))
code = n.phone_pair_start()["code"]
n.PHONE_PAIRING["expires"] = time.time() - 1
check("expired code refused", raises(n.phone_pair_finish, code, PHONE, "S24 Ultra"))
code = n.phone_pair_start()["code"]
wrong = "%04d" % ((int(code) + 1) % 10000)
for _ in range(5):
    raises(n.phone_pair_finish, wrong, PHONE, "S24 Ultra")
check("code dies after five wrong tries", raises(n.phone_pair_finish, code, PHONE, "S24 Ultra"))
code = n.phone_pair_start()["code"]
check("bad device id refused", raises(n.phone_pair_finish, code, "../x", "S24 Ultra"))
n.phone_forget(PHONE)
check("forget revokes", n.phone_device_for_token(token) is None)

# --- Task 2: the listener and its gate -------------------------------------------
import urllib.request, urllib.error
PORT = 8799
BASE = "http://127.0.0.1:%d" % PORT

def call(method, path, token=None, body=None, headers=None, raw=None):
    """(status, headers, bytes), errors returned rather than raised."""
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
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

n.phone_link_start(PORT, "127.0.0.1")
code = n.phone_pair_start()["code"]
st, _h, body = call("POST", "/phone/pair", body={"code": code, "device_id": PHONE, "name": "S24 Ultra"})
token = json.loads(body).get("token") if st == 200 else None
check("pairing over the wire", st == 200 and token, (st, body[:120]))
st0 = call("GET", "/phone/hello")[0]
st1, _h, body = call("GET", "/phone/hello", token)
check("hello needs the token", st0 == 401 and st1 == 200
      and json.loads(body).get("version") == n.APP_VERSION, (st0, st1, body[:120]))
desk = [call("GET", p, token)[0] for p in ("/", "/api/status", "/api/library/status")] + \
       [call("POST", p, token, body={})[0] for p in ("/api/sorter/aside", "/api/play")]
check("desktop routes don't exist here, token or not", desk == [404] * 5, desk)
code = n.phone_pair_start()["code"]
wrong = "%04d" % ((int(code) + 1) % 10000)
st = call("POST", "/phone/pair", body={"code": wrong, "device_id": PHONE, "name": "S24"})[0]
check("wrong code over the wire is 403", st == 403, st)
n.phone_link_stop()
try:
    call("GET", "/phone/hello", token); closed = False
except urllib.error.URLError as exc:
    closed = isinstance(exc.reason, ConnectionRefusedError) or "refused" in str(exc).lower()
check("stop closes the port", closed)
n.phone_link_start(PORT, "127.0.0.1")      # back up for what follows

# --- Task 3: snapshot and downloads ------------------------------------------------
film_path = os.path.join(WORK, "phone_film.mkv")
ep_path = os.path.join(WORK, "phone_ep.mkv")
data = bytes(range(256)) * (3 * 4096)               # 3 MiB, every byte position distinct mod 256
open(film_path, "wb").write(data)
open(ep_path, "wb").write(bytes(range(256)) * 4096)  # 1 MiB
conn = n.db()
cur = conn.execute("INSERT INTO movies (path,title,year,tmdb_id) VALUES (?,?,?,?)",
                   (film_path, "Phone Test Film", 2020, "999001"))
film_id = cur.lastrowid
cur = conn.execute("INSERT INTO shows (name,title,tmdb_id) VALUES (?,?,?)",
                   ("phone test show", "Phone Test Show", "999002"))
conn.execute("INSERT INTO episodes (path,show_id,season,episode) VALUES (?,?,?,?)",
             (ep_path, cur.lastrowid, 1, 2))
conn.commit(); conn.close()

st, _h, body = call("GET", "/phone/snapshot", token)
snap = json.loads(body) if st == 200 else {}
fm = next((m for m in snap.get("movies") or [] if m.get("tmdb_id") == "999001"), {})
ep = next((e for e in snap.get("episodes") or [] if e.get("show_tmdb_id") == "999002"), {})
check("snapshot has keys", fm.get("key") == "m999001" and fm.get("ext") == ".mkv"
      and ep.get("key") == "e999002s1e2", (st, fm.get("key"), fm.get("ext"), ep.get("key")))
st, h, body = call("GET", "/phone/file?key=m999001", token)
check("whole file", st == 200 and body == data and int(h["Content-Length"]) == len(data)
      and h.get("Accept-Ranges") == "bytes", (st, len(body)))
st, h, body = call("GET", "/phone/file?key=m999001", token, headers={"Range": "bytes=1048576-"})
check("resume from the middle", st == 206 and body == data[1048576:]
      and h.get("Content-Range") == "bytes 1048576-3145727/3145728", (st, h.get("Content-Range")))
st, h, body = call("GET", "/phone/file?key=m999001", token, headers={"Range": "bytes=10-19"})
check("a slice", st == 206 and body == data[10:20], (st, len(body)))
bad = []
for rng in ("bytes=999999999-", "bytes=abc", "bytes=5-2"):
    st, h, _b = call("GET", "/phone/file?key=m999001", token, headers={"Range": rng})
    bad.append((st, h.get("Content-Range")))
check("bad ranges are 416", bad == [(416, "bytes */3145728")] * 3, bad)
st = call("GET", "/phone/file?key=m1", token)[0]
check("unknown key is 404", st == 404, st)
os.remove(ep_path)
st, _h, body = call("GET", "/phone/file?key=e999002s1e2", token)
check("missing file is 404", st == 404 and b"isn't on the drive" in body, (st, body))
check("snapshot needs the token", call("GET", "/phone/snapshot")[0] == 401)

# --- Task 4: sync exchange -------------------------------------------------------------
n.CONFIG["sync_folder"] = ""
n.log_event("movie", film_id, "Phone Test Film", "rated", value=8)
st, h, body = call("GET", "/phone/sync", token)
lines = [json.loads(l) for l in body.decode("utf-8").splitlines() if l.strip()] if st == 200 else []
check("PC events go to the phone", any(l.get("tmdb") == "999001" and l.get("event") == "rated"
                                       for l in lines), (st, len(lines)))
mac = {"v": 1, "uid": "macuid1", "utc": time.time() - 50, "device_id": "mac0000000000000",
       "device": "MacBook", "kind": "movie", "tmdb": "999001", "event": "watchlisted"}
conn = n.db()
conn.execute("INSERT OR IGNORE INTO sync_inbox (uid,device_id,device,utc,payload,applied)"
             " VALUES (?,?,?,?,?,1)", (mac["uid"], mac["device_id"], "MacBook", mac["utc"],
                                        json.dumps(mac)))
conn.commit(); conn.close()
body = call("GET", "/phone/sync", token)[2].decode("utf-8")
check("Mac events are relayed", '"macuid1"' in body)

def phone_line(uid, device_id, value):
    return json.dumps({"v": 1, "uid": uid, "utc": time.time() + 1, "device_id": device_id,
                       "device": "S24", "kind": "movie", "tmdb": "999001", "season": None,
                       "episode": None, "show": None, "title": "Phone Test Film",
                       "event": "rated", "value": value, "seconds": None,
                       "position": None, "total": None}) + "\n"

st, _h, body = call("POST", "/phone/sync", token, raw=phone_line("phoneuid1", PHONE, 9).encode())
conn = n.db()
rating = conn.execute("SELECT userrating FROM movies WHERE id=?", (film_id,)).fetchone()[0]
conn.close()
check("phone events land on the PC", st == 200 and json.loads(body).get("kept") == 1 and rating == 9,
      (st, body, rating))
raw = (phone_line("spoof1", n.sync_device_id(), 2) + phone_line("spoof2", "mac0000000000000", 2)).encode()
st, _h, body = call("POST", "/phone/sync", token, raw=raw)
check("foreign device lines dropped", st == 200 and json.loads(body).get("kept") == 0, body)
st = call("POST", "/phone/sync", token, raw=b"x", headers={"Content-Length": str(21 * 1024 * 1024)})[0]
check("oversized upload refused", st == 413, st)
check("cloud folder untouched when sharing is off",
      os.path.isfile(os.path.join(n.PHONE_SYNC_DIR, "device-%s.jsonl" % PHONE)))

# --- Task 5: being found -------------------------------------------------------------
import socket
def shout(msg, wait):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(wait)
    try:
        s.sendto(msg, ("127.0.0.1", PORT))
        return s.recvfrom(4096)[0]
    except (socket.timeout, ConnectionResetError):
        return None
    finally:
        s.close()

reply = shout(b"NEXTUP?", 2)
info = json.loads(reply) if reply else {}
check("answers the call", info.get("nextup") == 1 and info.get("port") == PORT
      and info.get("version") == n.APP_VERSION, info)
check("ignores anything else", shout(b"hello", 0.5) is None)
n.phone_link_stop()
check("silent once stopped", shout(b"NEXTUP?", 0.5) is None)

# --- Task 6: Settings, through the desktop routes ---------------------------------------
import subprocess, threading
from http.server import ThreadingHTTPServer
n.PHONE_PORT = PORT
n.PHONE_HOST = "127.0.0.1"          # never every interface from a test: that's a firewall prompt
desk = ThreadingHTTPServer(("127.0.0.1", 8798), n.Handler)
threading.Thread(target=desk.serve_forever, daemon=True).start()
def desk_call(method, path, body=None):
    req = urllib.request.Request("http://127.0.0.1:8798" + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None)
    def parse(b):
        try:
            return json.loads(b or b"{}")
        except ValueError:
            return {}           # an HTML error page: the route isn't there
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, parse(r.read())
    except urllib.error.HTTPError as e:
        return e.code, parse(e.read())

def hello_status(tok=None):
    """The phone port's answer, or 0 when nothing is listening."""
    try:
        return call("GET", "/phone/hello", tok)[0]
    except urllib.error.URLError:
        return 0

st, state = desk_call("POST", "/api/phone/enable", {"on": True})
up = hello_status()
check("enable starts the listener, and remembers", st == 200 and up == 401 and state.get("enabled")
      and n.phone_cfg()["enabled"], (st, up, state.get("enabled")))
st, pair = desk_call("POST", "/api/phone/pair")
code = pair.get("code") or ""
try:
    st2, _h, body = call("POST", "/phone/pair", body={"code": code, "device_id": PHONE, "name": "S24 Ultra"})
except urllib.error.URLError:
    st2, body = 0, b"{}"
token = json.loads(body).get("token") if st2 == 200 else ""
state = desk_call("GET", "/api/phone")[1]
state.setdefault("devices", [])
check("a code from Settings pairs a phone, listed by name",
      re.fullmatch(r"\d{4}", code) and token and [d["name"] for d in state["devices"]] == ["S24 Ultra"],
      (code, st2, state.get("devices")))
check("state hides secrets", token not in json.dumps(state) and "token_sha" not in json.dumps(state)
      and state.get("port") == PORT, state)
desk_call("POST", "/api/phone/forget", {"id": PHONE})
check("forget from Settings locks it out", token and hello_status(token) == 401)
desk_call("POST", "/api/phone/enable", {"on": False})
check("turning it off closes the port, and remembers",
      hello_status() == 0 and not n.phone_cfg()["enabled"])
desk.shutdown()

# --- final review fixes -------------------------------------------------------------------
import http.client
n.phone_link_start(PORT, "127.0.0.1")
code = n.phone_pair_start()["code"]
token = n.phone_pair_finish(code, PHONE, "S24 Ultra")

# 1: a filename outside Latin-1 still downloads, named properly
odd = os.path.join(WORK, "Don’t Look Up – 2021.mkv")
open(odd, "wb").write(b"x" * 1000)
conn = n.db()
conn.execute("INSERT INTO movies (path,title,year,tmdb_id) VALUES (?,?,?,?)",
             (odd, "Don't Look Up", 2021, "999003"))
conn.commit(); conn.close()
try:
    st, h, body = call("GET", "/phone/file?key=m999003", token)
    disp = h.get("Content-Disposition") or ""
except Exception as exc:              # the bug: an error body inside a promised film
    st, body, disp = repr(exc)[:80], b"", ""
check("a curly-quoted filename downloads whole", st == 200 and body == b"x" * 1000
      and "filename*=UTF-8''" in disp, (st, len(body), disp))

# 2: a phone can't take another device's name — but a forgotten phone can come back
check("a forgotten phone can pair again", token)
code = n.phone_pair_start()["code"]
why = raises(n.phone_pair_finish, code, n.sync_device_id(), "evil")
check("can't pair as this PC", isinstance(why, str) and "already" in why, why)
code = n.phone_pair_start()["code"]
conn = n.db()
conn.execute("INSERT OR IGNORE INTO sync_devices (device_id,name,events,last_utc,file_mtime)"
             " VALUES ('cafe000000000000','MacBook',1,0,0)")
conn.commit(); conn.close()
why = raises(n.phone_pair_finish, code, "cafe000000000000", "evil")
check("can't pair as a device already sharing (the Mac)", isinstance(why, str) and "already" in why, why)

# 3: a failure writing the sync file is answered, not dropped
real_receive = n.phone_receive
def locked(device, text):
    raise PermissionError(13, "The process cannot access the file because it is being used")
n.phone_receive = locked
try:
    st, _h, body = call("POST", "/phone/sync", token, raw=b"\n")
    answered = (st, json.loads(body).get("error"))
except Exception as exc:
    answered = (0, repr(exc))
n.phone_receive = real_receive
check("a locked sync file gets a 503 with a reason", answered[0] == 503 and answered[1], answered)

# 4: a phone file with a line inserted part way still gets read in full
later = phone_line("ins_b", PHONE, 7)
call("POST", "/phone/sync", token, raw=later.encode())
call("POST", "/phone/sync", token, raw=(phone_line("ins_a", PHONE, 6) + later).encode())
conn = n.db()
got = conn.execute("SELECT COUNT(*) FROM history WHERE uid='ins_a'").fetchone()[0]
conn.close()
check("an event inserted earlier in the phone's file isn't skipped", got == 1, got)

# 5: turning it off ends connections already open, not just new ones
c = http.client.HTTPConnection("127.0.0.1", PORT, timeout=5)
c.request("GET", "/phone/hello", headers={"Authorization": "Bearer " + token})
first = c.getresponse(); first.read()
n.phone_link_stop()
try:
    c.request("GET", "/phone/hello", headers={"Authorization": "Bearer " + token})
    second = c.getresponse().status
except Exception:
    second = None
c.close()
check("off means off, even mid-connection", first.status == 200 and second is None, (first.status, second))

js = "\n;\n".join(re.findall(r"<script>(.*?)</script>", n.PAGE, re.S))
open(os.path.join(WORK, "page.js"), "w", encoding="utf-8").write(js)
r = subprocess.run(["node", "-e", "new Function(require('fs').readFileSync(process.argv[1],'utf8'));console.log('ok')",
                    os.path.join(WORK, "page.js")], capture_output=True, text=True)
check("page script parses", r.stdout.strip() == "ok", r.stderr[:300])
check("the page has the phone card", 'id="phone_body"' in n.PAGE)

print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
