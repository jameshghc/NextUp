"""A show whose episodes have all gone stops being a tile.

The sorter merges release folders ("Futurama S05") into the show they belong
to, and the scan dropped the episodes but kept the show row — a blank tile
with nothing to play. This builds a fake TV folder, scans it, takes files
away and scans again. A show you'd marked (here, rated) is kept anyway."""
import sys, os, shutil, tempfile
sys.path.insert(0, r"X:\NextUp"); os.chdir(r"X:\NextUp"); sys.argv = ["nextup.py"]
import nextup as n
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from devserve import isolate
SANDBOX = os.path.join(tempfile.gettempdir(), "nextup_emptyshows")
isolate(n, SANDBOX)

results = []
def check(name, ok, detail=""):
    ok = bool(ok); results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- %s" % (detail,)) if detail != "" else ""))

# An empty library, not the copy: the copy's paths are all on E:, and a scan
# of this fake folder would read every one of them as deleted.
os.remove(n.DB_PATH)
n._MIGRATED[0] = False
n.LIB.loaded_at = 0
n.CONFIG["tmdb_key"] = ""            # no lookups; the rows are what's tested

TV = os.path.join(here, "_work", "empty_shows_tv")
shutil.rmtree(TV, ignore_errors=True)

def episode(show, name):
    path = os.path.join(TV, show, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.truncate(51 * 1024 * 1024)   # over the scan's 50 MB sample floor
    return path

episode("Kept Show", "Kept.Show.S01E01.mkv")
gone = episode("Gone Show", "Gone.Show.S01E01.mkv")
rated = episode("Rated Show", "Rated.Show.S01E01.mkv")
n.CONFIG["media_folders"] = [TV]

def shows():
    conn = n.db()
    try:
        return sorted(r["title"] for r in conn.execute("SELECT title FROM shows"))
    finally:
        conn.close()

n.scan_local_library()
check("first scan finds three shows", shows() == ["Gone Show", "Kept Show", "Rated Show"], shows())

conn = n.db()
conn.execute("UPDATE shows SET userrating=8 WHERE title='Rated Show'")
conn.commit(); conn.close()

shutil.rmtree(os.path.dirname(gone))
shutil.rmtree(os.path.dirname(rated))
n.scan_local_library()
after = shows()
check("a show with no episodes left is gone", "Gone Show" not in after, after)
check("a show you rated is kept even with no episodes", "Rated Show" in after, after)
check("a show still on disk is untouched", "Kept Show" in after, after)

n.LIB.loaded_at = 0
tiles = n.browse_library("tv", "", "title", "all", 400, 0)["items"]
check("and the grid has no empty tile", [t["title"] for t in tiles] == ["Kept Show", "Rated Show"],
      [t["title"] for t in tiles])

shutil.rmtree(TV, ignore_errors=True)
print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
