"""Does the port come free the moment the window closes, and does a second
copy wait rather than refusing?"""
import sys, os, time, tempfile, socket, threading, json, urllib.request
sys.path.insert(0, r"X:\NextUp"); os.chdir(r"X:\NextUp"); sys.argv = ["nextup.py"]
import nextup as n
here = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(here, "_work")      # scratch output, never committed
os.makedirs(WORK, exist_ok=True)
sys.path.insert(0, here)
from devserve import isolate
isolate(n, os.path.join(tempfile.gettempdir(), "nextup_porttest"))
from http.server import ThreadingHTTPServer

results = []
def check(name, ok, detail=""):
    ok = bool(ok); results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- %s" % (detail,)) if detail != "" else ""))

PORT = 8799
srv = ThreadingHTTPServer(("127.0.0.1", PORT), n.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.3)
check("a running server shows the port as in use", n.port_in_use(PORT))
with urllib.request.urlopen("http://127.0.0.1:%d/api/status" % PORT, timeout=5) as r:
    check("and answers as this app", "version" in json.loads(r.read()))

t0 = time.time()
n.release_port(srv)
dt = time.time() - t0
check("release_port frees it", not n.port_in_use(PORT), "took %.2fs" % dt)
check("and it frees it quickly", dt < 1.5, "%.2fs" % dt)
# the socket is really gone: a fresh server can take the port
try:
    srv2 = ThreadingHTTPServer(("127.0.0.1", PORT), n.Handler); srv2.server_close(); ok = True
except OSError as exc:
    ok = False
check("a new copy can bind the port straight away", ok)
n.release_port(srv)
check("calling it twice is harmless", True)

# waiting rather than refusing
# A real server that ACCEPTS: a raw listen(1) socket that never accepts
# starts refusing probes once its queue fills, and then looks free.
busy = ThreadingHTTPServer(("127.0.0.1", PORT), n.Handler)
threading.Thread(target=busy.serve_forever, daemon=True).start()
time.sleep(0.3)
t0 = time.time()
got = n.wait_for_port(PORT, seconds=1)
check("wait_for_port gives up when something really holds the port", not got, "%.1fs" % (time.time() - t0))
def free_it():
    time.sleep(1.2); n.release_port(busy)
threading.Thread(target=free_it, daemon=True).start()
t0 = time.time()
got = n.wait_for_port(PORT, seconds=6)
check("and returns as soon as it comes free", got and (time.time() - t0) < 3, "%.1fs" % (time.time() - t0))

# the cache is only written when something changed
n.CACHE_PATH = os.path.join(tempfile.gettempdir(), "nextup_porttest", "cache.json")
n._CACHE_DIRTY[0] = True
t0 = time.time(); n.cache_flush(); first = time.time() - t0
t0 = time.time(); n.cache_flush(); second = time.time() - t0
check("an unchanged cache is not rewritten on close", second < 0.05 and first > 0.1,
      "changed %.2fs, unchanged %.3fs" % (first, second))
size_before = os.path.getsize(n.CACHE_PATH)
n.CACHE["http://example/KEY"] = {"x": 1}; n._CACHE_DIRTY[0] = True
n.cache_flush()
check("a changed cache still is", os.path.getsize(n.CACHE_PATH) != size_before)
print("\n%d/%d passed" % (sum(results), len(results)))
