"""End to end: the app's own startup path on a spare port, closed the way
the window's close button closes it, timing when the port comes free.

Runs headless (no pywebview window) but through main()'s real server setup
and the real shutdown sequence, against a sandbox copy of everything.
"""
import sys, os, time, tempfile, threading, json, urllib.request, socket
sys.path.insert(0, r"X:\NextUp"); os.chdir(r"X:\NextUp"); sys.argv = ["nextup.py"]
import nextup as n
here = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(here, "_work")      # scratch output, never committed
os.makedirs(WORK, exist_ok=True)
sys.path.insert(0, here)
from devserve import isolate
isolate(n, os.path.join(tempfile.gettempdir(), "nextup_porte2e"))
from http.server import ThreadingHTTPServer

PORT = 8798
n.APP_PORT = PORT
url = "http://127.0.0.1:%d" % PORT
results = []
def check(name, ok, detail=""):
    ok = bool(ok); results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- %s" % (detail,)) if detail != "" else ""))

# --- the app, as main() starts it -------------------------------------------
server = ThreadingHTTPServer(("127.0.0.1", PORT), n.Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
threading.Thread(target=n.playback_monitor, daemon=True).start()
time.sleep(0.4)
check("app is up and answering", n.already_running(url))

# make the cache dirty and pretend a channel is playing, so the close has
# real work to do — this is the worst case, not the easy one
n._CACHE_DIRTY[0] = True
n.LIB.load(force=True)
film = n.LIB.movies[0]
slow = {"n": 0}
def slow_taskkill(*a, **k):
    slow["n"] += 1
    time.sleep(3.0)          # mpv taking its time to go
    return None
n.stop_current_playback = slow_taskkill
n.mpv_command = lambda *a: None
n.mpv_get = lambda *a, **k: None
n.NOW_PLAYING.update(type="movie", id=film["movieid"], title=film["title"],
                     started_at=time.time() - 600, channel="Comedy #5",
                     channel_id="comedy", position=300, duration=6000)

# --- close it, the way the window's close button does ------------------------
t0 = time.time()
n.release_port(server)           # what window_closing does first
freed = time.time() - t0
check("port is free before any of the tidying up", not n.port_in_use(PORT), "%.2fs after the click" % freed)
n.shutdown_playback()
n.cache_flush()
total = time.time() - t0
check("the slow part happened AFTER the port was free", slow["n"] == 1 and total > 3,
      "tidying took %.1fs in total" % total)

# --- a second copy, started in that window -----------------------------------
try:
    again = ThreadingHTTPServer(("127.0.0.1", PORT), n.Handler)
    again.server_close(); ok = True
except OSError:
    ok = False
check("a second copy can take the port immediately", ok)

# --- and the old behaviour's worst case: port held, not answering -------------
blocker = ThreadingHTTPServer(("127.0.0.1", PORT), n.Handler)
threading.Thread(target=blocker.serve_forever, daemon=True).start()
time.sleep(0.2)
def let_go():
    time.sleep(2.0); n.release_port(blocker)
threading.Thread(target=let_go, daemon=True).start()
t0 = time.time()
ok = n.wait_for_port(PORT, seconds=n.PORT_WAIT_SECONDS)
check("a copy started too early waits for the old one instead of refusing",
      ok, "waited %.1fs" % (time.time() - t0))
print("\n%d/%d passed" % (sum(results), len(results)))
