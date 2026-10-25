"""The Library's Home: Quick Suggest (the better episodes of shows you like
that you haven't seen in a month, and films you rated highly that you
haven't seen in six) and Continue (TV and films mixed, newest first). The
app opens on it. Against a sandbox copy (devserve.isolate)."""
import sys, os, time, tempfile
sys.path.insert(0, r"X:\NextUp"); os.chdir(r"X:\NextUp"); sys.argv = ["nextup.py"]
import nextup as n
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from devserve import isolate
isolate(n, os.path.join(tempfile.gettempdir(), "nextup_home"))

results = []
def check(name, ok, detail=""):
    ok = bool(ok); results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- %s" % (detail,)) if detail != "" else ""))

def ago(days):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - days * 86400))

# A clean slate of likes, so only what's set up here can be suggested.
conn = n.db()
conn.execute("UPDATE shows SET userrating=0, favourited_at=NULL")
conn.execute("UPDATE movies SET userrating=0, favourited_at=NULL, last_played=NULL, resume_pos=0")
conn.execute("UPDATE episodes SET userrating=0, last_played=NULL, resume_pos=0")
show = conn.execute("INSERT INTO shows (name,title,tmdb_id,tmdb_rating,userrating) VALUES "
                    "('liked','Liked Show','990101',8.0,9)").lastrowid
def ep(k, rating, votes, last=None):
    return conn.execute("INSERT INTO episodes (path,show_id,season,episode,title,runtime,tmdb_rating,tmdb_votes,last_played)"
                        " VALUES (?,?,1,?,?,1500,?,?,?)", ("X:/lk/%d.mkv" % k, show, k, "Ep %d" % k, rating, votes, last)).lastrowid
top = ep(1, 9.6, 400, ago(10))         # the best, but seen ten days ago
second = ep(2, 9.2, 400, ago(90))      # next best, seen three months ago: this one
ep(3, 7.0, 400)
ep(4, 6.5, 400)
meh = conn.execute("INSERT INTO shows (name,title,tmdb_id,tmdb_rating,userrating) VALUES "
                   "('meh','Meh Show','990102',8.0,5)").lastrowid
conn.execute("INSERT INTO episodes (path,show_id,season,episode,title,runtime,tmdb_rating,tmdb_votes)"
             " VALUES ('X:/meh/1.mkv',?,1,1,'M',1500,9.9,900)", (meh,))
films = [r[0] for r in conn.execute("SELECT id FROM movies ORDER BY id LIMIT 3")]
conn.execute("UPDATE movies SET userrating=9, last_played=? WHERE id=?", (ago(400), films[0]))   # loved, long ago
conn.execute("UPDATE movies SET userrating=9, last_played=? WHERE id=?", (ago(10), films[1]))    # loved, just seen
conn.execute("UPDATE movies SET userrating=6 WHERE id=?", (films[2],))                            # only liked
conn.commit(); conn.close()
n.LIB.loaded_at = 0; n.LOCAL.loaded_at = 0

home = n.build_home()
sug = home["suggest"]
eps = [s for s in sug if s["type"] == "episode"]
fms = [s for s in sug if s["type"] == "movie"]
check("Quick Suggest: a show you like gives its best episode not seen in 30 days",
      [e["id"] for e in eps if e["show_id"] == show] == [second], [(e["title"], e["sub"]) for e in eps])
check("not from a show you don't much like", not any(e["show_id"] == meh for e in eps))
check("films you rated highly and haven't seen in six months, not one just seen or only liked",
      films[0] in [f["id"] for f in fms] and films[1] not in [f["id"] for f in fms]
      and films[2] not in [f["id"] for f in fms], [f["title"] for f in fms])
check("at most 8, every one with a title and something to play", len(sug) <= 8
      and all(s.get("title") and s.get("id") for s in sug), len(sug))
wild = [x for x in sug if x.get("wild")]
check("about 15% are wildcards, picked from the whole library, not by rating: at least one",
      1 <= len(wild) <= max(1, round(len(sug) * 0.25)) and all(x.get("id") for x in wild),
      [(x["title"], x["type"]) for x in wild])
check("a wildcard isn't one of the rated picks twice over", len(set((x["type"], x["id"]) for x in sug)) == len(sug))
check("the same day, the same suggestions", [s["id"] for s in n.build_home()["suggest"]] == [s["id"] for s in sug])

# Continue: TV and films mixed, newest first.
conn = n.db()
conn.execute("UPDATE movies SET resume_pos=1200, resume_total=6000, last_played=? WHERE id=?", (ago(3), films[0]))
conn.execute("UPDATE episodes SET resume_pos=600, resume_total=1500, last_played=? WHERE id=?", (ago(1), second))
conn.commit(); conn.close()
n.LIB.loaded_at = 0; n.LOCAL.loaded_at = 0
cont = n.build_home()["continue"]
order = [(c["type"], c["id"]) for c in cont]
check("Continue mixes TV and films, the most recent first",
      ("episode", second) in order and ("movie", films[0]) in order
      and order.index(("episode", second)) < order.index(("movie", films[0])), order[:4])
check("at most 8", len(cont) <= 8)

# The page.
pg = n.PAGE
check("the page: a house before Films, Home as the Library's own panel, and where the Library opens",
      "['home','Home']" in pg and "home:'#view-home'" in pg and 'id="view-home"' in pg
      and "let libSection = 'home';" in pg)
check("the page: wildcards aren't labelled (asked); the rows say Loading while they come",
      "'wildcard'" not in pg and "Loading" in pg[pg.find("async function loadHome("):][:600])
check("the page: the wheel over a Home row never scrolls the page", "wheelSideways(strip, true)" in pg
      and "if(max <= 0 && !hold) return;" in pg)
check("the page: two rows, Quick Suggest and Continue, a tile plays",
      "Quick Suggest" in pg and "function loadHome(" in pg and "'tile hometile'" in pg)

print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
