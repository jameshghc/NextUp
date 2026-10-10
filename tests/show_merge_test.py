"""One show, however many folders it's in: X-Men '97 was two shows because
"x-men 97" (a dotted release in the films folder) and "x-men '97" (the TV
folder) are different names, though TMDB says they're the same show.

Against a COPY of the real library, which has exactly that in it. Nothing
on disk is touched: file sizes are read, never written."""
import sys, os, tempfile
sys.path.insert(0, r"X:\NextUp"); os.chdir(r"X:\NextUp"); sys.argv = ["nextup.py"]
import nextup as n
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from devserve import isolate
isolate(n, os.path.join(tempfile.gettempdir(), "nextup_showmerge"))

results = []
def check(name, ok, detail=""):
    ok = bool(ok); results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- %s" % (detail,)) if detail != "" else ""))

check("names that differ only in punctuation are one show",
      n.show_key("x-men 97") == n.show_key("x-men '97") == n.show_key("X-Men: '97")
      and n.show_key("x-men 97") != n.show_key("x-men 98"))

# --- a pair made here, so the test doesn't rest on one show in one library -------------
WORK = os.path.join(here, "_work", "showmerge")
os.makedirs(WORK, exist_ok=True)
def make(name, size):
    p = os.path.join(WORK, name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as fh:
        fh.truncate(size)
    return p
# Two folders, as X-Men '97 had: a release folder and the tidy one.
small = make(os.path.join("release", "dup.s01e01.small.mkv"), 1000)
big = make(os.path.join("tidy", "dup.s01e01.big.mkv"), 5000)
only = make(os.path.join("tidy", "dup.s01e02.mkv"), 2000)
# Two parts of one episode number in ONE folder, SpongeBob-style: not copies.
part_a = make(os.path.join("parts", "toon.s01e17a.mkv"), 1000)
part_b = make(os.path.join("parts", "toon.s01e17b.mkv"), 3000)
conn = n.db()
a = conn.execute("INSERT INTO shows (name,title,tmdb_id,matched,userrating,rated_at) VALUES"
                 " ('dup show','Dup Show','dup1',1,8.5,'2026-08-03 12:00:00')").lastrowid
b = conn.execute("INSERT INTO shows (name,title,tmdb_id,matched,favourited_at) VALUES"
                 " ('dup show!','Dup Show','dup1',1,'2026-09-01 10:00:00')").lastrowid
e_small = conn.execute("INSERT INTO episodes (path,show_id,season,episode,resume_pos,resume_total,last_played)"
                       " VALUES (?,?,1,1,600,1800,'2026-10-01 20:00:00')", (small, a)).lastrowid
e_big = conn.execute("INSERT INTO episodes (path,show_id,season,episode) VALUES (?,?,1,1)", (big, b)).lastrowid
e_only = conn.execute("INSERT INTO episodes (path,show_id,season,episode) VALUES (?,?,1,2)", (only, b)).lastrowid
conn.execute("INSERT INTO history (at,kind,item_id,title,event,value) VALUES"
             " ('2026-08-03 12:00:00','tvshow',?,'Dup Show','rated',8.5)", (a,))
conn.execute("INSERT INTO history (at,kind,item_id,title,event,position) VALUES"
             " ('2026-10-01 20:00:00','episode',?,'Dup Show','stopped',600)", (e_small,))
conn.execute("INSERT INTO queue (pos,kind,item_id,added_at) VALUES (1,'tvshow',?,'now')", (a,))
toon = conn.execute("INSERT INTO shows (name,title,tmdb_id,matched) VALUES ('toon','Toon','toon1',1)").lastrowid
for pth in (part_a, part_b):
    conn.execute("INSERT INTO episodes (path,show_id,season,episode) VALUES (?,?,1,17)", (pth, toon))
conn.commit()

merged = n.merge_duplicate_shows(conn)
rows = conn.execute("SELECT * FROM shows WHERE tmdb_id='dup1'").fetchall()
check("two shows with one TMDB id become one", len(rows) == 1, len(rows))
keep = rows[0]
check("your rating and your favourite both come through",
      keep["userrating"] == 8.5 and keep["favourited_at"], (keep["userrating"], keep["favourited_at"]))
eps = conn.execute("SELECT * FROM episodes WHERE show_id=? ORDER BY season, episode", (keep["id"],)).fetchall()
check("one of each episode", [(e["season"], e["episode"]) for e in eps] == [(1, 1), (1, 2)],
      [(e["season"], e["episode"], e["path"]) for e in eps])
check("the bigger file is the one kept", eps[0]["path"] == big, eps[0]["path"])
check("with where you'd got to on the other copy", eps[0]["resume_pos"] == 600, eps[0]["resume_pos"])
ign = [r[0] for r in conn.execute("SELECT path FROM ignored_files")]
check("the smaller copy is set aside, so a rescan doesn't bring it back", small in ign, ign)
h = conn.execute("SELECT kind, item_id FROM history WHERE title='Dup Show' ORDER BY id").fetchall()
check("history follows: the rating to the show kept, the sitting to the episode kept",
      [tuple(r) for r in h] == [("tvshow", keep["id"]), ("episode", eps[0]["id"])], [tuple(r) for r in h])
q = conn.execute("SELECT item_id FROM queue WHERE kind='tvshow'").fetchall()
check("and the queue", [r[0] for r in q] == [keep["id"]], [r[0] for r in q])
check("two parts of one number in one folder are both kept",
      conn.execute("SELECT COUNT(*) FROM episodes WHERE show_id=?", (toon,)).fetchone()[0] == 2)
# At least the pair made here; the copy of the real library adds X-Men '97 (1 and 4).
check("it says what it did", merged.get("shows") >= 1 and merged.get("episodes") >= 1, merged)
check("again, nothing more to do", n.merge_duplicate_shows(conn) == {"shows": 0, "episodes": 0})

# --- the real one ---------------------------------------------------------------------------
xm = conn.execute("SELECT * FROM shows WHERE tmdb_id='138502'").fetchall()
check("X-Men '97 is one show", len(xm) == 1, [(r["id"], r["name"]) for r in xm])
if xm:
    xeps = conn.execute("SELECT season, episode FROM episodes WHERE show_id=? ORDER BY season, episode",
                        (xm[0]["id"],)).fetchall()
    codes = [(r[0], r[1]) for r in xeps]
    check("with every episode once: season 1 whole, season 2 to E09",
          codes == [(1, i) for i in range(1, 11)] + [(2, i) for i in range(1, 10)], codes)
    check("and your 8.5 on it", xm[0]["userrating"] == 8.5, xm[0]["userrating"])
conn.close()

check("a scan merges as it goes, and start-up catches a library from before",
      "merge_duplicate_shows(conn)" in __import__("inspect").getsource(n.scan_local_library)
      and "merge_duplicate_shows" in __import__("inspect").getsource(n.prepare_app))

print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
