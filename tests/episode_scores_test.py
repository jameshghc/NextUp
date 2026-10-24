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

# --- Task 2: the scores -----------------------------------------------------------------
conn = n.db()
show = conn.execute("INSERT INTO shows (name,title,tmdb_id,tmdb_rating) VALUES ('graded','Graded','880002',7.0)").lastrowid
def ep(season, number, rating, votes):
    return conn.execute("INSERT INTO episodes (path,show_id,season,episode,title,runtime,tmdb_rating,tmdb_votes)"
                        " VALUES (?,?,?,?,?,1800,?,?)",
                        ("X:/gr/s%de%d.mkv" % (season, number), show, season, number, "E%d" % number,
                         rating, votes)).lastrowid
g1, g2, g3, g4 = ep(1, 1, 8.0, 500), ep(1, 2, 9.5, 3), ep(1, 3, 6.0, 400), ep(1, 4, 0, 0)
sp = ep(0, 1, 9.9, 900)
dull = conn.execute("INSERT INTO shows (name,title,tmdb_id,tmdb_rating) VALUES ('blank','Blank','880003',0)").lastrowid
conn.execute("INSERT INTO episodes (path,show_id,season,episode,title,runtime,tmdb_rating,tmdb_votes)"
             " VALUES ('X:/bl/1.mkv',?,1,1,'x',1800,0,0)", (dull,))
conn.commit(); conn.close()
def reload():
    n.LIB.loaded_at = 0; n.LOCAL.loaded_at = 0; n.LIB.load()
def setsql(sql, *a):
    c = n.db(); c.execute(sql, a); c.commit(); c.close(); reload()
reload()

sc = n.episode_scores(show)
check("a well-voted episode keeps TMDB's rating", sc.get(g1) == 8.0, sc)
mean_n = (8.0 * 500 + 6.0 * 400) / 900.0
check("few votes: pulled towards the neighbours", mean_n < sc.get(g2, 0) < 9.5 and sc[g2] - mean_n < 9.5 - sc[g2],
      (round(mean_n, 2), sc.get(g2)))
season_mean = (8.0 * 500 + 9.5 * 3 + 6.0 * 400) / 903.0
check("no votes: the season's average", abs(sc.get(g4, 0) - season_mean) <= 0.05, (round(season_mean, 2), sc.get(g4)))
setsql("UPDATE episodes SET userrating=10 WHERE id=?", g3)
check("your own rating wins", n.episode_scores(show).get(g3) == 10.0)
setsql("UPDATE shows SET userrating=9 WHERE id=?", show)
check("your show rating nudges a quarter of the way", n.episode_scores(show).get(g1) == 8.5, n.episode_scores(show).get(g1))
setsql("UPDATE shows SET userrating=0 WHERE id=?", show)
for _ in range(3):
    setsql("INSERT INTO history (at,kind,item_id,title,event) VALUES ('2026-10-01 20:00:00','episode',?,'E1','watched')", g1)
check("rewatched: +0.3 a time after the first", n.episode_scores(show).get(g1) == 8.6, n.episode_scores(show).get(g1))
for _ in range(3):
    setsql("INSERT INTO history (at,kind,item_id,title,event) VALUES ('2026-10-01 20:00:00','episode',?,'E1','watched')", g1)
check("and capped", n.episode_scores(show).get(g1) == 8.9, n.episode_scores(show).get(g1))
setsql("UPDATE episodes SET tmdb_rating=12 WHERE id=?", g1)
check("never above 10", n.episode_scores(show).get(g1) == 10.0, n.episode_scores(show).get(g1))
setsql("UPDATE episodes SET tmdb_rating=8.0 WHERE id=?", g1)
setsql("DELETE FROM history WHERE kind='episode' AND item_id=?", g1)
sc = n.episode_scores(show)
ss = n.season_scores(show, sc)
w = {g1: 500, g2: 3, g3: 100, g4: 1}
expect = round(sum(sc[k] * w[k] for k in w) / float(sum(w.values())), 1)
check("a season is its episodes, vote-weighted (yours count as 100)", ss.get(1) == expect, (ss.get(1), expect))
check("specials are scored, on their own", 0 in ss and ss[0] == sc.get(sp), ss)
check("nothing to go on: no scores", n.episode_scores(dull) == {}, n.episode_scores(dull))

# --- Task 3: on the show's page ----------------------------------------------------------
conn = n.db()
g5, g6 = ep(1, 5, 7.0, 100), ep(1, 6, 8.8, 300)
conn.commit(); conn.close()
reload()
for _ in range(2):
    setsql("INSERT INTO history (at,kind,item_id,title,event) VALUES ('2026-10-01 20:00:00','episode',?,'E1','watched')", g1)
d = n.show_detail(show)
eps = {e["id"]: e for s_ in d["seasons"] for e in s_["episodes"]}
check("show_detail: a score on every episode it can score", eps[g1]["score"] is not None and eps[g6]["score"] == 8.8,
      {k: v["score"] for k, v in eps.items()})
check("and on every season", all(s_.get("score") is not None for s_ in d["seasons"]),
      [(s_["season"], s_.get("score")) for s_ in d["seasons"]])
best = [e["id"] for e in d.get("best") or []]
check("Best episodes: five, highest first, no specials", len(best) == 5 and sp not in best and best[0] == g3,
      [(eps[b]["code"], eps[b]["score"]) for b in best])
check("a star for one you rated highly or keep coming back to", eps[g3]["star"] and eps[g1]["star"] and not eps[g5]["star"],
      {k: v["star"] for k, v in eps.items()})
check("'good in theory': unwatched, unrated and near the top", eps[g6]["gem"] and not eps[g3]["gem"] and not eps[g5]["gem"],
      {k: v["gem"] for k, v in eps.items()})
dd = n.show_detail(dull)
check("a show with nothing to go on looks as it did",
      all(e["score"] is None for s_ in dd["seasons"] for e in s_["episodes"])
      and not dd.get("best") and all(s_.get("score") is None for s_ in dd["seasons"]), dd.get("best"))

print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
