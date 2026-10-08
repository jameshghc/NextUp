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

import re, subprocess
WORK = os.path.join(here, "_work"); os.makedirs(WORK, exist_ok=True)
js = "\n;\n".join(re.findall(r"<script>(.*?)</script>", n.PAGE, re.S))
open(os.path.join(WORK, "page.js"), "w", encoding="utf-8").write(js)
r = subprocess.run(["node", "-e", "new Function(require('fs').readFileSync(process.argv[1],'utf8'));console.log('ok')",
                    os.path.join(WORK, "page.js")], capture_output=True, text=True)
check("page script parses", r.stdout.strip() == "ok", r.stderr[:300])
check("Settings has the plugged-in phone section", 'id="usbphone_body"' in n.PAGE
      and "SEND MY LIBRARY" in n.PAGE)

print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
