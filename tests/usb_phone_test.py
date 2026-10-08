"""The phone over USB, from the desktop app: seeing it, and SEND MY LIBRARY.

No phone and no adb here: adb is a fake that answers like the real one, and
the phone app is a small server that records what it was sent. The one
promise checked hardest is the user's: sending the library sends the
catalogue and the TMDB key, and never a video file."""
import sys, os, json, time, tempfile, threading
sys.path.insert(0, r"X:\NextUp"); os.chdir(r"X:\NextUp"); sys.argv = ["nextup.py"]
import nextup as n
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from devserve import isolate
isolate(n, os.path.join(tempfile.gettempdir(), "nextup_usbphone"))
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

results = []
def check(name, ok, detail=""):
    ok = bool(ok); results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- %s" % (detail,)) if detail != "" else ""))

# --- a pretend phone app -----------------------------------------------------------
got = []
class FakePhone(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def reply(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200); self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        got.append(("GET", self.path, None))
        self.reply({"version": "0.1.49", "connected": True})
    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        got.append(("POST", self.path, json.loads(raw or b"{}")))
        self.reply({"ok": True, "imported": {"movies": 3, "shows": 2, "episodes": 9, "art": 0}})
phone = ThreadingHTTPServer(("127.0.0.1", 0), FakePhone)
threading.Thread(target=phone.serve_forever, daemon=True).start()
PHONE_PORT = phone.server_address[1]

# --- a pretend adb -------------------------------------------------------------------
calls = []
SCRIPT = {"devices": "List of devices attached\n", "running": True, "installed": True}
def fake_adb(*args, timeout=15):
    calls.append(args)
    a = list(args)
    if a[:1] == ["devices"]:
        return SCRIPT["devices"]
    if "-s" in a:
        a = a[a.index("-s") + 2:]
    if a[:2] == ["shell", "settings"]:
        return "James's S21 Ultra\n"
    if a[:2] == ["shell", "getprop"]:
        return "SM-G998B\n"
    if a[:2] == ["shell", "df"]:
        return "Filesystem 1K-blocks Used Available Use% Mounted on\n/dev/fuse 485000000 395000000 90177536 82% /storage/emulated\n"
    if a[:3] == ["shell", "pm", "list"]:
        return "package:app.nextup.mobile\n" if SCRIPT["installed"] else ""
    if a[:2] == ["shell", "pidof"]:
        return "12345\n" if SCRIPT["running"] else ""
    if a[:1] == ["forward"] and a[1:2] == ["--remove"]:
        return ""
    if a[:1] == ["forward"]:
        return "%d\n" % PHONE_PORT
    return ""
n.usb_adb = fake_adb
n.usb_adb_path = lambda: r"C:\fake\adb.exe"

# --- seeing the phone ----------------------------------------------------------------
st = n.usb_phone_state()
check("no phone plugged in is said", not st["found"] and "plugged in" in st["why"], st)
SCRIPT["devices"] = "List of devices attached\nR5CR11XSBFX\tunauthorized usb:1-1 transport_id:3\n"
st = n.usb_phone_state()
check("an unanswered USB debugging prompt is said", not st["found"] and "Allow" in st["why"], st)
SCRIPT["devices"] = "List of devices attached\nR5CR11XSBFX\tdevice usb:1-1 product:p3sxeea model:SM_G998B transport_id:3\n"
st = n.usb_phone_state()
check("a phone is seen by its own name, with its free space",
      st["found"] and st["name"] == "James's S21 Ultra" and 85 <= st["free_gb"] <= 87
      and st["app_installed"] and st["app_running"], st)
n.usb_adb_path = lambda: None
st = n.usb_phone_state()
check("without adb, it says what's missing", not st["found"] and "adb" in st["why"], st)
n.usb_adb_path = lambda: r"C:\fake\adb.exe"

# --- SEND MY LIBRARY ----------------------------------------------------------------
SCRIPT["running"] = False
try:
    n.usb_send_library(); refused = None
except n.AppError as exc:
    refused = str(exc)
check("needs the phone app open", refused and "Open Next Up on the phone" in refused, refused)
SCRIPT["running"] = True
n.CONFIG["tmdb_key"] = "test-key-123"
calls.clear(); got.clear()
result = n.usb_send_library()
posts = {p: body for m, p, body in got if m == "POST"}
snap = (posts.get("/api/library/snapshot/import") or {}).get("snapshot") or {}
want = n.build_library_snapshot()
check("the whole catalogue goes", snap.get("kind") == "nextup-library-snapshot"
      and len(snap.get("movies") or []) == len(want["movies"]) > 0, len(snap.get("movies") or []))
check("the TMDB key goes, so the phone can identify its own films",
      (posts.get("/api/config") or {}).get("tmdb_key") == "test-key-123", posts.get("/api/config"))
check("the phone then scans its own folder", "/api/library/scan" in posts, list(posts))
check("and NOT ONE video file is sent", not any(c and c[0] in ("push", "install", "sync")
                                                or "push" in c for c in calls), calls)
check("the result says what arrived", result.get("movies") == 3 and result.get("shows") == 2, result)
check("the tunnel is taken down after", any(c[:2] == ("forward", "--remove") or
                                            (len(c) > 2 and c[2:4] == ("forward", "--remove")) for c in calls), calls)

# --- the routes the page uses ---------------------------------------------------------
desk = ThreadingHTTPServer(("127.0.0.1", 8789), n.Handler)
threading.Thread(target=desk.serve_forever, daemon=True).start()
import urllib.request
def desk_call(method, path):
    req = urllib.request.Request("http://127.0.0.1:8789" + path, method=method,
                                 data=b"{}" if method == "POST" else None)
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())
s = desk_call("GET", "/api/usbphone")
check("the page can ask what's plugged in", s.get("found") and s.get("name"), s)
desk_call("POST", "/api/usbphone/send")
for _ in range(100):
    s = desk_call("GET", "/api/usbphone")
    if not (s.get("send") or {}).get("running"):
        break
    time.sleep(0.1)
check("sending runs in the background and reports back", (s.get("send") or {}).get("result"), s.get("send"))
desk.shutdown(); phone.shutdown()

# --- the Show filter: what's on this device, and what isn't ------------------------------
n.import_library_snapshot({"kind": "nextup-library-snapshot", "version": 1, "device": "DESKTOP-TEST",
                           "exported_at": "2026-10-08 12:00:00", "app_version": n.APP_VERSION,
                           "movies": [{"tmdb_id": "x999001", "title": "Elsewhere Film", "year": 2001,
                                       "genres": "", "directors": "", "cast_names": "", "plot": "",
                                       "poster": None, "tmdb_rating": 7.0, "runtime": 100,
                                       "userrating": 0, "playcount": 0}],
                           "shows": [], "episodes": []}, fetch_art=False)
local = n.browse_library("film", "", "title", "here", 400, 0)["items"]
away = n.browse_library("film", "", "title", "elsewhere", 400, 0)["items"]
check("On this device shows only what's here", local and not any(i.get("elsewhere") for i in local),
      len(local))
check("Not on this device shows only what isn't", [i["title"] for i in away] == ["Elsewhere Film"],
      [i["title"] for i in away][:5])

import re, subprocess
WORK =os.path.join(here, "_work"); os.makedirs(WORK, exist_ok=True)
js = "\n;\n".join(re.findall(r"<script>(.*?)</script>", n.PAGE, re.S))
open(os.path.join(WORK, "page.js"), "w", encoding="utf-8").write(js)
r = subprocess.run(["node", "-e", "new Function(require('fs').readFileSync(process.argv[1],'utf8'));console.log('ok')",
                    os.path.join(WORK, "page.js")], capture_output=True, text=True)
check("page script parses", r.stdout.strip() == "ok", r.stderr[:300])
check("Settings has the plugged-in phone section", 'id="usbphone_body"' in n.PAGE
      and "SEND MY LIBRARY" in n.PAGE)
check("the Show list offers Show all and On this device",
      '<option value="all">Show all</option>' in n.PAGE and '<option value="here">' in n.PAGE)
check("and no longer offers Not rated yet, Rated, Favourites or Not on this device",
      not any('<option value="%s">' % v in n.PAGE for v in ("unrated", "rated", "favourite", "elsewhere")))
conn = n.db()
fav_ids = [r[0] for r in conn.execute("SELECT id FROM movies ORDER BY id LIMIT 2")]
conn.execute("UPDATE movies SET favourited_at='2026-10-08 12:00:00' WHERE id IN (?,?)", fav_ids)
conn.commit(); conn.close()
n.LIB.loaded_at = 0
both = n.browse_library("all", "", "title", "favourite+here", 400, 0)["items"]
check("Favourites and On this device together", both and all(i.get("favourited") and not i.get("elsewhere")
                                                             for i in both), [i["title"] for i in both])

# --- your ratings come with the library, onto what's on the phone too ---------------------
conn = n.db()
def film(tmdb, rating=0, plays=0):
    return conn.execute("INSERT INTO movies (path,title,year,tmdb_id,userrating,playcount) VALUES (?,?,?,?,?,?)",
                        ("/phone/%s.mkv" % tmdb, "Film " + tmdb, 2000, tmdb, rating, plays)).lastrowid
unrated, own = film("r1"), film("r2", rating=4)
show = conn.execute("INSERT INTO shows (name,title,tmdb_id,userrating) VALUES (?,?,?,?)",
                    ("rshow", "Rated Show", "r9", 0)).lastrowid
conn.commit()
events_before = conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]
conn.close()
def snap_film(tmdb, rating, plays=0):
    return {"tmdb_id": tmdb, "title": "Film " + tmdb, "year": 2000, "genres": "", "directors": "",
            "cast_names": "", "plot": "", "poster": None, "tmdb_rating": 7.0, "runtime": 100,
            "userrating": rating, "playcount": plays}
n.import_library_snapshot({"kind": "nextup-library-snapshot", "version": 1, "device": "DESKTOP-TEST",
                           "exported_at": "2026-10-08 12:00:00", "app_version": n.APP_VERSION,
                           "movies": [snap_film("r1", 8, plays=2), snap_film("r2", 9), snap_film("r3", 7.5)],
                           "shows": [{"tmdb_id": "r9", "title": "Rated Show", "year": 2000, "genres": "",
                                      "plot": "", "poster": None, "tmdb_rating": 7, "userrating": 6,
                                      "episode_count": 0}],
                           "episodes": []}, fetch_art=False)
def field(table, rid, col):
    c = n.db(); v = c.execute("SELECT %s FROM %s WHERE id=?" % (col, table), (rid,)).fetchone()[0]; c.close(); return v
check("a film on the phone takes your rating from the PC", field("movies", unrated, "userrating") == 8,
      field("movies", unrated, "userrating"))
check("and that you've watched it", field("movies", unrated, "playcount") == 2, field("movies", unrated, "playcount"))
check("a show too", field("shows", show, "userrating") == 6, field("shows", show, "userrating"))
check("a rating made on the phone is never overwritten", field("movies", own, "userrating") == 4,
      field("movies", own, "userrating"))
# A film copied over after the library was sent: picked up by the next scan.
conn = n.db(); later = film("r3"); conn.commit(); conn.close()
n.adopt_snapshot_marks()
check("a film copied over later takes its rating at the next scan", field("movies", later, "userrating") == 7.5,
      field("movies", later, "userrating"))
import inspect
check("the scan does that", "adopt_snapshot_marks()" in inspect.getsource(n.library_scan_worker))
c = n.db(); after = c.execute("SELECT COUNT(*) FROM history").fetchone()[0]; c.close()
check("copied ratings aren't new ratings: nothing added to your history", after == events_before,
      (events_before, after))

print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
