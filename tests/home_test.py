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
check("at most 11, every one with a title and something to play", len(sug) <= 11
      and all(s.get("title") and s.get("id") for s in sug), len(sug))
wild = [x for x in sug if x.get("wild")]
check("three wildcards, picked from the whole library, not by rating",
      len(wild) == 3 and all(x.get("id") for x in wild),
      [(x["title"], x["type"]) for x in wild])
check("a wildcard isn't one of the rated picks twice over", len(set((x["type"], x["id"]) for x in sug)) == len(sug))
check("the same day, the same suggestions", [s["id"] for s in n.build_home()["suggest"]] == [s["id"] for s in sug])

# Three lists, a visit at a time (2026-10-25): Favourites (as above), Deeper
# cuts (good, not the top) and Pot luck (mostly chance) — not every visit
# leaning on the top scores.
lists = home.get("suggest_lists") or []
check("three Quick Suggest lists", len(lists) == 3 and all(len(l) <= 11 for l in lists), [len(l) for l in lists])
check("the first is the favourites", [x["id"] for x in lists[0]] == [x["id"] for x in sug] if lists else False)
check("each has its three wildcards", all(sum(1 for x in l if x.get("wild")) == 3 for l in lists),
      [sum(1 for x in l if x.get("wild")) for l in lists])
_all = [(x["type"], x["id"]) for l in lists for x in l]
check("nothing appears in two lists", len(_all) == len(set(_all)), len(_all) - len(set(_all)))
_deep = [x["id"] for x in lists[1] if x["type"] == "episode" and x.get("show_id") == show] if len(lists) > 1 else []
check("Deeper cuts doesn't give the liked show's top pick again", second not in _deep, _deep)
check("the page: each visit takes the next list, and shuffles it",
      "suggest_lists" in n.PAGE and "nextup.homeList" in n.PAGE)

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
check("Continue: as many as Quick Suggest, at most", len(cont) <= n.HOME_SUGGEST and n.HOME_CONTINUE == n.HOME_SUGGEST)

# The page.
pg = n.PAGE
check("the page: a house before Films, Home as the Library's own panel, and where the Library opens",
      "['home','Home']" in pg and "home:'#view-home'" in pg and 'id="view-home"' in pg
      and "let libSection = 'home';" in pg)
check("the page: wildcards aren't labelled (asked); the rows say Loading while they come",
      "'wildcard'" not in pg and "Loading" in pg[pg.find("async function loadHome("):][:600])
check("the page: the wheel over a Home row never scrolls the page", "wheelSideways(strip, true)" in pg
      and "if(max <= 0 && !hold) return;" in pg)
check("the page: on the PC the tiles size themselves so both rows fit the window",
      "function sizeHome(" in pg and "var(--home-tile," in pg and "sizeHome();" in pg)
check("the page: Quick Suggest in a new order every time it loads", "shuffleInPlace(" in pg
      and "shuffleInPlace(d.suggest" in pg)
check("the page: Continue's heading opens History", "homehead homelink" in pg)
_sr = pg[pg.find('<div class="searchrow">'):][:1200]
check("the Library's toolbar: Sort, then Show, then the search box",
      0 < _sr.find('id="libsort"') < _sr.find('id="shelf"') < _sr.find('id="q"'), "")
check("the page: two rows, Quick Suggest and Continue, a tile plays",
      "Quick Suggest" in pg and "function loadHome(" in pg and "'tile hometile'" in pg)

# 2026-10-26: on the phone, Home is drawn again from the PC's library once
# the PC is found, not left with the phone's own few films.
check("the phone's Home follows the PC link", "homeFromPc = !!fromPc && !!d && !d.error;" in pg
      and "if(homeFromPc !== null && homeFromPc !== !!up) loadHome();" in pg[pg.find("function pcLinkSet("):][:900])

# 2026-10-26, the phone: Home fits the screen, its tiles peek like the
# Library's, and the PC's items carry what's needed to play them.
check("the phone sizes Home to the screen too", "(rows[0].clientWidth - 2 * 10) / 2.5" in pg
      and "if(document.body.classList.contains('android')) return;\n  const v = $('#view-home');" not in pg)
check("a tap peeks, a second opens the details", "if(b.classList.contains('peeking')) return details();" in pg
      and "el('div', 'homepeek')" in pg)
_src = open(n.__file__, encoding="utf-8").read()
check("the PC's Home items carry their identity for the phone",
      'suggest=[_for_phone(i) for i in home.get("suggest") or []]' in _src)
check("the phone's settings and Library toolbar fit the width",
      "body.android .apgrid{grid-template-columns:minmax(0,1fr)" in pg
      and "body.android #view-library .searchrow .searchbox{flex:1 1 100%;max-width:none}" in pg)
check("the house sits under the word Library on the phone", "function alignLibNav()" in pg
      and "alignLibNav();\n}" in pg)

# --- 2026-10-27: Ratings, the Library's place for what you've rated -------------------
_k = n.db()
_ids = [r[0] for r in _k.execute("SELECT id FROM movies WHERE genres LIKE '%Comedy%' ORDER BY id LIMIT 14")]
for _x, _id in enumerate(_ids):
    _k.execute("UPDATE movies SET userrating=?, rated_at='2026-10-0%d 20:00:00' WHERE id=?" % (1 + _x % 9),
               (6 + (_x % 8) * 0.5, _id))
_k.commit(); _k.close()
n.LIB.load(force=True)
fame = n.build_hall_of_fame()
cats = fame["categories"]
ids = [c["id"] for c in cats]
check("the Hall of Fame has shelves", len(cats) >= 3 and ids[0] == "top", ids[:5])
check("no shelf is thin", all(c["count"] >= 3 for c in cats) and all(c["count"] == len(c["items"]) for c in cats))
top = next(c for c in cats if c["id"] == "top")
check("your top twelve is twelve, best first", len(top["items"]) <= 12
      and [i["score"] for i in top["items"]] == sorted((i["score"] for i in top["items"]), reverse=True))
check("each item has what a poster and its page need",
      all({"kind", "id", "tmdb", "title", "score", "art"} <= set(i) for c in cats for i in c["items"]))
check("genre shelves only for genres with five or more",
      all(c["count"] >= n.FAME_MIN for c in cats if c["id"].startswith("genre:")))
check("directors once each, the Coens not twice",
      len({frozenset(i["id"] for i in c["items"]) for c in cats if c["id"].startswith("dir:")})
      == len([c for c in cats if c["id"].startswith("dir:")]))
check("Rate has left the menu for the Library", 'data-view="rate"' not in pg
      and "['ratings','Ratings']" in pg and "ratings:'#view-ratings'" in pg)
check("it sits between History and Recommendations",
      "[['history','History'],['ratings','Ratings'],['recs','Recommendations']]" in pg)
check("Hall of Fame and Rate, one switch", 'data-mode="fame"' in pg and 'data-mode="rate"' in pg
      and 'id="view-rate"' in pg and "function drawFameShelf(" in pg)
check("a shelf shows twelve before SHOW ALL, under a header that stays put",
      "c.items.slice(0, 12)" in pg and 'class="rattop"' in pg and ".rattop{position:sticky" in pg
      and 'id="fameback"' in pg[pg.find('class="rattop"'):][:700])
check("Ratings has no scroll bar, and its header wears the page's own background",
      "#view-library > #view-ratings::-webkit-scrollbar{display:none}" in pg
      and "body.glass .rattop{background:" in pg)
check("a shelf opens at its first row", "fameOpen = c.id; drawFame(); $('#view-ratings').scrollTop = 0;" in pg)
check("pressing Ratings goes back to the Hall of Fame's front",
      "if(id === 'ratings'){ ratMode = 'fame'; fameOpen = null; }" in pg)
check("the phone asks the PC for its shelves", "/api/pcfame" in pg
      and '"/api/pcfame": "/phone/fame"' in open(n.__file__, encoding="utf-8").read())

print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
