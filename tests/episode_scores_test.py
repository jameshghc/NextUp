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
    {"episode_number": 1, "name": "A", "overview": "It begins.", "still_path": None, "runtime": 30,
     "vote_average": 8.4, "vote_count": 120, "air_date": "2019-04-23",
     "crew": [{"job": "Director", "name": "Alice Dee"}, {"job": "Writer", "name": "Bob Wry"},
              {"job": "Writer", "name": "Cat Pen"}, {"job": "Editor", "name": "Ed Cut"}],
     "guest_stars": [{"name": "Guest One"}, {"name": "Guest Two"}]},
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
show_mean = (8.0 * 500 + 9.5 * 3 + 6.0 * 400) / 903.0
check("few votes: barely moved from the show's usual", show_mean < sc.get(g2, 0) < 9.5
      and sc[g2] - show_mean < 9.5 - sc[g2], (round(show_mean, 2), sc.get(g2)))
check("no votes: the show's usual", abs(sc.get(g4, 0) - show_mean) <= 0.05, (round(show_mean, 2), sc.get(g4)))
setsql("UPDATE episodes SET userrating=10 WHERE id=?", g3)
check("your own rating wins", n.episode_scores(show).get(g3) == 10.0)
setsql("UPDATE shows SET userrating=9 WHERE id=?", show)
_want = round(9 + (8.0 - show_mean) * 500 / 520.0, 1)
check("your show rating is where its episodes start", n.episode_scores(show).get(g1) == _want,
      (n.episode_scores(show).get(g1), _want))
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
check("show_detail: a score on every episode it can score",
      eps[g1]["score"] is not None and eps[g6]["score"] > eps[g5]["score"],
      {k: v["score"] for k, v in eps.items()})
check("and on every season", all(s_.get("score") is not None for s_ in d["seasons"]),
      [(s_["season"], s_.get("score")) for s_ in d["seasons"]])
best = [e["id"] for e in d.get("best") or []]
check("Best episodes: five, highest first, no specials", len(best) == 5 and sp not in best and best[0] == g3,
      [(eps[b]["code"], eps[b]["score"]) for b in best])
check("and each of them says so on its own row", sorted(k for k, v in eps.items() if v.get("best")) == sorted(best),
      [k for k, v in eps.items() if v.get("best")])
check("a star for one you rated highly or keep coming back to", eps[g3]["star"] and eps[g1]["star"] and not eps[g5]["star"],
      {k: v["star"] for k, v in eps.items()})
check("'good in theory': unwatched, unrated and near the top", eps[g6]["gem"] and not eps[g3]["gem"] and not eps[g5]["gem"],
      {k: v["gem"] for k, v in eps.items()})
dd = n.show_detail(dull)
check("a show with nothing to go on looks as it did",
      all(e["score"] is None for s_ in dd["seasons"] for e in s_["episodes"])
      and not dd.get("best") and all(s_.get("score") is None for s_ in dd["seasons"]), dd.get("best"))

# --- Task 4: Non-stop Favs: TV leans to the better episodes -------------------------------
setsql("UPDATE shows SET favourited_at=NULL")
setsql("UPDATE movies SET favourited_at=NULL")
setsql("UPDATE shows SET favourited_at='2026-10-01 20:00:00' WHERE id=?", show)
favstv = next(c for c in n.CHANNELS if c["id"] == "favstv")
plain = dict(favstv); plain.pop("weight_by_score", None)
weighted = n.channel_blocks(favstv)
unweighted = n.channel_blocks(plain)
count = lambda blocks, eid: sum(1 for b in blocks if eid in (b.get("episode_ids") or []))
check("better blocks come round more often",
      count(weighted, g3) > count(weighted, g5) and count(weighted, g3) == 3, (count(weighted, g3), count(weighted, g5)))
ids = lambda blocks: set(tuple(b.get("episode_ids") or []) for b in blocks)
check("every block still comes round", ids(weighted) == ids(unweighted), (len(ids(weighted)), len(ids(unweighted))))
check("the same day, the same order", [b["sub"] for b in n.channel_blocks(favstv)] == [b["sub"] for b in weighted])
setsql("UPDATE shows SET favourited_at=NULL WHERE id=?", show)
setsql("UPDATE shows SET favourited_at='2026-10-01 20:00:00' WHERE id=?", dull)
check("a show with no scores builds as before", len(n.channel_blocks(favstv)) == len(n.channel_blocks(plain)))
check("only the TV favourites channel is weighted",
      [c["id"] for c in n.CHANNELS if c.get("weight_by_score")] == ["favstv"])

# --- Final review fixes --------------------------------------------------------------------
# I1: a show TMDB rates as a whole, but whose episodes nobody has voted on
# yet (every show, until the first scan after this) — no made-up scores.
conn = n.db()
flat = conn.execute("INSERT INTO shows (name,title,tmdb_id,tmdb_rating) VALUES ('flat','Flat','880004',7.5)").lastrowid
for k in range(1, 7):
    conn.execute("INSERT INTO episodes (path,show_id,season,episode,title,runtime,tmdb_rating,tmdb_votes)"
                 " VALUES (?,?,1,?,?,1800,0,0)", ("X:/fl/%d.mkv" % k, flat, k, "F%d" % k))
conn.commit(); conn.close()
reload()
fd = n.show_detail(flat)
check("no votes anywhere: no scores, no marks, no Best row",
      n.episode_scores(flat) == {} and not fd["best"]
      and all(e["score"] is None and not e["gem"] for s_ in fd["seasons"] for e in s_["episodes"]),
      n.episode_scores(flat))
# A season nobody's voted on yet, in a show that otherwise has votes.
conn = n.db()
fresh = [conn.execute("INSERT INTO episodes (path,show_id,season,episode,title,runtime,tmdb_rating,tmdb_votes)"
                      " VALUES (?,?,2,?,?,1800,0,0)", ("X:/gr/s2e%d.mkv" % k, show, k, "N%d" % k)).lastrowid
         for k in (1, 2)]
conn.commit(); conn.close()
reload()
gd = n.show_detail(show)
s2 = next(s_ for s_ in gd["seasons"] if s_["season"] == 2)
check("a season nobody's voted on gets no chip", s2.get("score") is None, s2.get("score"))
best_ids = [e["id"] for e in gd["best"]]
check("and its fallback scores never reach Best or 'good in theory'",
      not any(f in best_ids for f in fresh) and not any(e["gem"] for e in s2["episodes"]), best_ids)
# I2: the channel's order holds through a rewatch.
setsql("UPDATE shows SET favourited_at=NULL")
setsql("UPDATE shows SET favourited_at='2026-10-01 20:00:00' WHERE id=?", show)
before = [b["sub"] for b in n.channel_blocks(favstv)]
for _ in range(3):
    setsql("INSERT INTO history (at,kind,item_id,title,event) VALUES ('2026-10-02 20:00:00','episode',?,'E5','watched')", g5)
check("Non-stop Favs: TV keeps its order through a rewatch", [b["sub"] for b in n.channel_blocks(favstv)] == before)
# I3: a scoring failure never takes the channels down.
_real = n.episode_scores
def _broken(*a, **k):
    raise RuntimeError("database is locked")
n.episode_scores = _broken
got = n.channel_blocks(favstv)
n.episode_scores = _real
check("a scoring error leaves the channel unweighted, not broken", len(got) == len(n.channel_blocks(plain)),
      (len(got), len(n.channel_blocks(plain))))

# --- Weighted to your rating (2026-10-24) ------------------------------------------------
# A show you love whose episodes only a handful voted on, harshly — I Think
# You Should Leave, in the user's library: 4-10 votes an episode, 4.6-7.4,
# show 7.0 on TMDB and 8.5 from you. Its episodes should sit near your 8.5.
conn = n.db()
itysl = conn.execute("INSERT INTO shows (name,title,tmdb_id,tmdb_rating,userrating) VALUES "
                     "('sketch','Sketch','880005',7.0,8.5)").lastrowid
sk = [conn.execute("INSERT INTO episodes (path,show_id,season,episode,title,runtime,tmdb_rating,tmdb_votes)"
                   " VALUES (?,?,1,?,?,1800,?,?)", ("X:/sk/%d.mkv" % k, itysl, k, "S%d" % k, r, v)).lastrowid
      for k, (r, v) in enumerate([(5.0, 5), (6.5, 10), (4.6, 5), (7.4, 5), (5.7, 6), (6.8, 6)], 1)]
conn.commit(); conn.close()
reload()
ks = n.episode_scores(itysl)
check("a show you rate 8.5 whose episodes few voted on: they sit near 8.5",
      all(8.0 <= ks[k] <= 9.0 for k in sk), [ks[k] for k in sk])
check("and still in TMDB's order", ks[sk[3]] == max(ks[k] for k in sk) and ks[sk[2]] == min(ks[k] for k in sk),
      [ks[k] for k in sk])
# Rating one yourself, from its score on the page.
check("the page: the score is a button that opens the rating bar for that episode",
      "rate_type: 'episode'" in n.PAGE and "'epscore'" in n.PAGE and "button" in n.PAGE[n.PAGE.find("function episodeRow("):][:3000])

# --- An episode's own details (2026-10-24) ------------------------------------------------
info = n.episode_info(e1)
check("an episode's details: plot, air date, director, writers, guest stars, TMDB's rating",
      info and info["plot"] == "It begins." and info["aired"] == "2019-04-23"
      and info["directors"] == ["Alice Dee"] and info["writers"] == ["Bob Wry", "Cat Pen"]
      and info["guests"] == ["Guest One", "Guest Two"] and info["tmdb_rating"] == 8.4 and info["tmdb_votes"] == 120,
      info)
check("an episode that isn't there: None", n.episode_info(99999999) is None)
_pe = n.PAGE[n.PAGE.find("function episodeRow("):][:4000]
check("the page: the star after the name, and the name opens the details",
      "'epbest'" in _pe and _pe.find("'epbest'") > _pe.find("eptitle") and "toggleEpisodeInfo(row, ep, d)" in _pe
      and "'epinfo'" in n.PAGE and "/api/episode?id=" in n.PAGE, "")

print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
