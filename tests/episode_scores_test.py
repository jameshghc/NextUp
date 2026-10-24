"""Season and episode scores: TMDB's per-episode ratings stored, the score
worked out from them, your ratings and your rewatches, shown on the show's
page, and Non-stop Favs: TV leaning to the better episodes. Against a
sandbox copy (devserve.isolate)."""
import sys, os, tempfile
sys.path.insert(0, r"X:\NextUp"); os.chdir(r"X:\NextUp"); sys.argv = ["nextup.py"]
import nextup as n
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from devserve import isolate
isolate(n, os.path.join(tempfile.gettempdir(), "nextup_epscores"))

results = []
def check(name, ok, detail=""):
    ok = bool(ok); results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- %s" % (detail,)) if detail != "" else ""))

# --- Task 1: TMDB's ratings, stored ---------------------------------------------------
calls = []
SEASON = {"episodes": [
    {"episode_number": 1, "name": "A", "overview": "", "still_path": None, "runtime": 30,
     "vote_average": 8.4, "vote_count": 120},
    {"episode_number": 2, "name": "B", "overview": "", "still_path": None, "runtime": 30,
     "vote_average": 6.1, "vote_count": 3}]}
def fake_tmdb(path, *a, **k):
    calls.append(path)
    return SEASON if path == "/tv/880001/season/1" else {}
n.tmdb = fake_tmdb
n.CONFIG["tmdb_key"] = n.CONFIG.get("tmdb_key") or "test"
conn = n.db()
sid = conn.execute("INSERT INTO shows (name,title,tmdb_id) VALUES ('score show','Score Show','880001')").lastrowid
e1 = conn.execute("INSERT INTO episodes (path,show_id,season,episode) VALUES ('X:/ss/e1.mkv',?,1,1)", (sid,)).lastrowid
e2 = conn.execute("INSERT INTO episodes (path,show_id,season,episode) VALUES ('X:/ss/e2.mkv',?,1,2)", (sid,)).lastrowid
conn.commit()
n.enrich_episode_titles(conn)
row = conn.execute("SELECT tmdb_rating, tmdb_votes FROM episodes WHERE id=?", (e1,)).fetchone()
check("episode ratings are stored", row and row["tmdb_rating"] == 8.4 and row["tmdb_votes"] == 120,
      row and tuple(row))
before = [c for c in calls if "880001" in c]
n.enrich_episode_titles(conn)
after = [c for c in calls if "880001" in c]
check("a season with ratings isn't fetched again", len(after) == len(before), (len(before), len(after)))
conn.close()
n.LIB.loaded_at = 0
n.LIB.load()
got = next((e for e in n.LIB.episodes if e.get("episodeid") == e1), {})
check("the library carries them", got.get("tmdb_rating") == 8.4 and got.get("tmdb_votes") == 120,
      {k: got.get(k) for k in ("tmdb_rating", "tmdb_votes")})

print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
