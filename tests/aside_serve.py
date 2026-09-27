"""devserve, pointed at the fake downloads folder with five copies waiting."""
import os, sys, shutil, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import devserve, nextup as n
from http.server import ThreadingHTTPServer
devserve.isolate(n, os.path.join(tempfile.gettempdir(), "nextup_aside_serve"))
SAND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_work", "fake_dupes")
n.CONFIG.update(downloads_folder=SAND)
BIN = os.path.join(SAND, "_bin"); os.makedirs(BIN, exist_ok=True)
n.send_to_trash = lambda p: shutil.move(p, os.path.join(BIN, os.path.basename(p))) and "Recycle Bin"
n.sorter_open_aside = lambda: print("  would open", os.path.join(SAND, "_DUPLICATES"), flush=True)
n.load_saved_recs()
print("aside serve on 8773", flush=True)
ThreadingHTTPServer(("127.0.0.1", 8773), n.Handler).serve_forever()
