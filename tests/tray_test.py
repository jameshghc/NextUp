"""Closing to the tray: the X hides the window rather than ending the app, so
the phone can keep reaching this PC; a tray icon brings it back or quits.
Against a sandbox copy (devserve.isolate), on port 8789. The icon itself is
put in the real tray for a moment and taken out again."""
import sys, os, json, time, tempfile, threading, urllib.request
sys.path.insert(0, r"X:\NextUp"); os.chdir(r"X:\NextUp"); sys.argv = ["nextup.py"]
import nextup as n
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from devserve import isolate
isolate(n, os.path.join(tempfile.gettempdir(), "nextup_tray"))

results = []
def check(name, ok, detail=""):
    ok = bool(ok); results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- %s" % (detail,)) if detail != "" else ""))

# --- the setting ---------------------------------------------------------------------
n.CONFIG.pop("tray_on_close", None)
check("on by default", n.tray_on_close() is True)
n.CONFIG["tray_on_close"] = False
check("and can be turned off", n.tray_on_close() is False)
n.CONFIG["tray_on_close"] = True

# --- what the X does -----------------------------------------------------------------
class FakeWindow:
    def __init__(self): self.calls = []
    def hide(self): self.calls.append("hide")
    def show(self): self.calls.append("show")
    def restore(self): self.calls.append("restore")
    def destroy(self): self.calls.append("destroy")

win = FakeWindow()
n._APP_WINDOW[0] = win
n.TRAY["running"] = True
told = []
n.TRAY["notify"] = lambda title, text: told.append(title)
n.CONFIG.pop("tray_told", None)
check("with the tray up, the X hides the window", n.close_to_tray() is True and win.calls == ["hide"], win.calls)
check("and says so the first time", len(told) == 1 and n.CONFIG.get("tray_told"), told)
n.close_to_tray()
check("but only the first time", len(told) == 1, told)
n.CONFIG["tray_on_close"] = False
check("turned off, the X closes the app", n.close_to_tray() is False)
n.CONFIG["tray_on_close"] = True
n.TRAY["running"] = False
check("no tray icon (it couldn't be made), the X closes the app", n.close_to_tray() is False)
n.TRAY["running"] = True
n.TRAY["quitting"] = True
check("Quit from the tray really quits", n.close_to_tray() is False)
n.TRAY["quitting"] = False

win.calls.clear()
n.show_app_window()
check("bringing it back shows and restores it", win.calls[:2] == ["show", "restore"], win.calls)

# --- the routes ------------------------------------------------------------------------
desk = n.ThreadingHTTPServer(("127.0.0.1", 8789), n.Handler)
threading.Thread(target=desk.serve_forever, daemon=True).start()
def call(path, body=None):
    req = urllib.request.Request("http://127.0.0.1:8789" + path,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 method="POST" if body is not None else "GET",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())
check("Settings reads it", call("/api/tray").get("on") is True)
got = call("/api/tray", {"on": False})
check("and saves it", got.get("on") is False
      and json.load(open(n.CONFIG_PATH, encoding="utf-8")).get("tray_on_close") is False, got)
call("/api/tray", {"on": True})
win.calls.clear()
check("a second copy opening asks this one to show its window",
      call("/api/window/show", {}).get("ok") and "show" in win.calls, win.calls)
check("the second copy knows how to ask", "/api/window/show" in open(n.__file__, encoding="utf-8").read()
      and callable(getattr(n, "show_running_copy", None)))

# --- the icon itself (Windows only) ----------------------------------------------------
if os.name == "nt":
    opened, quit_ = [], []
    tray = n.Tray(on_open=lambda: opened.append(1), on_quit=lambda: quit_.append(1))
    ok = tray.start(timeout=5)
    check("the icon goes into the tray", ok and n.TRAY["running"], ok)
    tray.command(n.Tray.OPEN)
    tray.command(n.Tray.QUIT)
    time.sleep(0.5)
    check("its Open and Quit do what they say", opened == [1] and quit_ == [1], (opened, quit_))
    tray.stop()
    time.sleep(0.3)
    check("and it comes out of the tray again", not n.TRAY["running"])

# --- the page ---------------------------------------------------------------------------
check("Settings has the switch", 'id="c_tray"' in n.PAGE)

desk.shutdown()
print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
