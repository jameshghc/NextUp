"""Three tags on every poster's phone peek: its genres (TV's doubled ones
split in two), topped up with TMDB's short keywords, then the decade.
Against a copy of the library, sandboxed."""
import sys, os, tempfile
sys.path.insert(0, r"X:\NextUp"); os.chdir(r"X:\NextUp"); sys.argv = ["nextup.py"]
import nextup as n
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from devserve import isolate
isolate(n, os.path.join(tempfile.gettempdir(), "nextup_tiletags"))

results = []
def check(name, ok, detail=""):
    ok = bool(ok); results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- %s" % (detail,)) if detail != "" else ""))

t = n.tile_tags
check("three genres are the three tags", t(["Drama", "History", "War"], ["slavery"], 2013)
      == ["Drama", "History", "War"], t(["Drama", "History", "War"], ["slavery"], 2013))
check("TV's doubled genres split in two", t(["Sci-Fi & Fantasy", "Animation"], [], 2024)
      == ["Science Fiction", "Fantasy", "Animation"], t(["Sci-Fi & Fantasy", "Animation"], [], 2024))
got = t(["Comedy"], ["based on memoir or autobiography", "high school", "time travel", "x"], 2009)
check("short of genres, short keywords top it up; long ones are skipped",
      got == ["Comedy", "high school", "time travel"], got)
got = t(["Drama"], [], 1994)
check("still short, the decade fills in", got[:2] == ["Drama", "1990s"], got)
got = t(["Documentary"], [], 1998, "tvshow")
check("and last, film or series: Weird Weekends has no keywords on TMDB at all",
      got == ["Documentary", "1990s", "series"], got)
check("a show's doubled genre counts as either half when choosing",
      n.genre_matches("Action", ["Action & Adventure"]) and n.genre_matches("Fantasy", ["Sci-Fi & Fantasy"])
      and not n.genre_matches("Comedy", ["Action & Adventure"]))
check("never a tag twice", t(["Action", "Action & Adventure"], ["action"], 2000).count("Action") == 1,
      t(["Action", "Action & Adventure"], ["action"], 2000))

# --- shows keep keywords, as films do ------------------------------------------------
conn = n.db()
cols = [r[1] for r in conn.execute("PRAGMA table_info(shows)")]
check("shows have a keywords column", "keywords" in cols, cols)
snap_cols = [r[1] for r in conn.execute("PRAGMA table_info(snapshot_movies)")] + \
            [r[1] for r in conn.execute("PRAGMA table_info(snapshot_shows)")]
check("so do the catalogue copies a phone holds", snap_cols.count("keywords") == 2, snap_cols)
check("TV's keyword list (results) is read as well as a film's (keywords)",
      n.keyword_names({"keywords": {"results": [{"name": "dystopia"}]}}) == ["dystopia"]
      and n.keyword_names({"keywords": {"keywords": [{"name": "heist"}]}}) == ["heist"])
check("show matching and the catch-up ask TMDB for keywords",
      '"credits,keywords"' in open(r"X:\NextUp\nextup.py", encoding="utf-8").read())
conn.execute("UPDATE shows SET keywords='mutant|superhero' WHERE id=(SELECT MIN(id) FROM shows)")
conn.execute("UPDATE movies SET keywords='heist|safecracker' WHERE id=(SELECT MIN(id) FROM movies)")
conn.commit(); conn.close()

# --- the catalogue carries them to the phone -----------------------------------------
snap = n.build_library_snapshot()
check("the library sent to a phone carries keywords",
      any(m.get("keywords") for m in snap["movies"]) and any(s.get("keywords") for s in snap["shows"]))

# --- every poster gets three -----------------------------------------------------------
n.LOCAL.loaded_at = 0; n.LIB.loaded_at = 0
items = n.browse_library("all", "", "title", "all", 2000, 0)["items"]
short = [(i["title"], i.get("tags")) for i in items if len(i.get("tags") or []) < 3]
# One film here has no genre and no keyword on TMDB at all — its decade and
# "film" are all there is to say. Anything with one genre gets three.
blank = [i for i in items if not i.get("genres")]
check("every poster with a genre has three tags", items and
      not [x for x in short if x[0] not in set(b["title"] for b in blank)], short[:5])

# --- Sort: Recently watched ------------------------------------------------------------
# Films by when they were last played; a show by its latest episode played;
# anything never watched after, alphabetically.
conn = n.db()
films = conn.execute("SELECT id FROM movies ORDER BY id LIMIT 2").fetchall()
show = conn.execute("SELECT show_id FROM episodes WHERE show_id IS NOT NULL LIMIT 1").fetchone()
conn.execute("UPDATE movies SET last_played=NULL"); conn.execute("UPDATE episodes SET last_played=NULL")
conn.execute("UPDATE movies SET last_played='2026-10-01 20:00:00' WHERE id=?", (films[0][0],))
conn.execute("UPDATE movies SET last_played='2026-10-21 20:00:00' WHERE id=?", (films[1][0],))
conn.execute("UPDATE episodes SET last_played='2026-10-10 20:00:00' WHERE id=(SELECT MIN(id) FROM episodes WHERE show_id=?)",
             (show[0],))
conn.commit(); conn.close()
n.LOCAL.loaded_at = 0; n.LIB.loaded_at = 0
got = n.browse_library("all", "", "watched", "all", 2000, 0)["items"]
top = [(i["kind"], i["id"]) for i in got[:3]]
check("Recently watched: newest first, films and shows together",
      top[0] == ("movie", films[1][0]) and top[1][0] == "tvshow" and top[2] == ("movie", films[0][0]), top)
rest = [i["title"] for i in got[3:40]]
check("and never-watched after, A to Z", rest == sorted(rest, key=n.norm_title), rest[:6])
check("the Sort list offers it", '<option value="watched">Recently watched</option>' in n.PAGE)

print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
