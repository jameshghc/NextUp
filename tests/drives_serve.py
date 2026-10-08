"""devserve, with a pretend drive to fill: for trying Library › Drives by
hand or by browser, copies and all, without a real drive or a real film.

The "drive" is a temp folder. Three small test films are added to the
sandbox library, and the copy refuses anything that isn't one of them — the
sandbox's library otherwise points at the real films on E:, and ticking one
of those must never start copying gigabytes."""
import os, sys, shutil, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import devserve, nextup as n
from http.server import ThreadingHTTPServer

real_worker = n.dock_copy_worker
devserve.isolate(n, os.path.join(tempfile.gettempdir(), "nextup_drives_serve"))
WORK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_work", "drives_serve")
shutil.rmtree(WORK, ignore_errors=True)
SRC, DRIVE = os.path.join(WORK, "films"), os.path.join(WORK, "TESTDRIVE")
os.makedirs(SRC); os.makedirs(DRIVE)

conn = n.db()
for title, year in (("Aardvark Test Film", 2001), ("Aardvark Second Test", 2002),
                    ("Aardvark Third Test", 2003)):
    path = os.path.join(SRC, "%s.%d.mkv" % (title.replace(" ", "."), year))
    with open(path, "wb") as fh:
        fh.truncate(51 * 1024 * 1024)            # over the samples floor, sparse
    conn.execute("INSERT INTO movies (path,title,year,tmdb_id) VALUES (?,?,?,?)",
                 (path, title, year, "ds%d" % year))
conn.commit(); conn.close()
# The second one is on the drive already, where the copy would put it.
already = os.path.join(DRIVE, "Films", "Aardvark Second Test (2002)")
os.makedirs(already)
with open(os.path.join(already, "Aardvark.Second.Test.2002.mkv"), "wb") as fh:
    fh.truncate(51 * 1024 * 1024)
n.LOCAL.loaded_at = 0; n.LIB.loaded_at = 0

n.list_dock_drives = lambda: [{"letter": DRIVE, "label": "TESTDRIVE", "removable": True,
                               "free": 900 * 1024 ** 3, "total": 1000 * 1024 ** 3}]


def guarded_worker(plan, dest_root):
    stray = [i for i in plan if not os.path.abspath(i["src"]).startswith(os.path.abspath(SRC))]
    if stray or os.path.abspath(dest_root) != os.path.abspath(DRIVE):
        n.DOCK.update(running=False, errors=["drives_serve: only the test films, only to "
                                             "TESTDRIVE (%d other file(s) refused)" % len(stray)])
        return
    real_worker(plan, dest_root)
n.dock_copy_worker = guarded_worker

n.load_saved_recs()
print("drives serve on 8775 — drive %s" % DRIVE, flush=True)
ThreadingHTTPServer(("127.0.0.1", 8775), n.Handler).serve_forever()
