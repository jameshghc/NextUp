"""The Recommendations home: rows dealt from the scan's pools, Refresh dealing
picks not shown before, a details page for things you don't own, and the
start-up check. TMDB is faked; the library is a sandboxed copy."""
import sys, os, json, tempfile, time, threading, urllib.request
sys.path.insert(0, r"X:\NextUp"); os.chdir(r"X:\NextUp"); sys.argv = ["nextup.py"]
import nextup as n
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from devserve import isolate
isolate(n, os.path.join(tempfile.gettempdir(), "nextup_rechome"))
# No real TMDB from here: a refill the home might ask for would otherwise run.
n.CONFIG["tmdb_key"] = ""

results = []
def check(name, ok, detail=""):
    ok = bool(ok); results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- %s" % (detail,)) if detail != "" else ""))

# --- what counts as a subject ---------------------------------------------------------
check("a mood isn't a subject", not any(n.is_subject_keyword(w) for w in
      ("suspenseful", "complex", "audacious", "intense", "dramatic", "inspirational")))
check("a thing is", all(n.is_subject_keyword(w) for w in
      ("space opera", "heist", "artificial intelligence (a.i.)", "time travel", "world war ii")))

# --- a pretend scan result -------------------------------------------------------------
def film(i, prefix="banger", **kw):
    d = {"key": "%s:%d" % (prefix, i), "id": str(900000 + i), "title": "Film %d" % i, "year": "2001",
         "rating": 7.5, "votes": 900, "genres": ["Drama"], "poster": None, "overview": "",
         "why": ["heists"]}
    d.update(kw)
    return d
def show(i):
    return dict(film(i, "tvrec", title="Show %d" % i), kind="tv")
n.LIB.load(force=True)
owned_tmdb = next(str(m["uniqueid"]["tmdb"]) for m in n.LIB.movies if (m.get("uniqueid") or {}).get("tmdb"))
films = [film(i) for i in range(20)]
films[3]["id"] = owned_tmdb                      # bought since the scan
n.DISMISSED.add("banger:5")                      # hidden by you
RESULT = {
    "has_key": True,
    "gaps": [{"key": "show:%d" % (100 + i), "title": "Gap Show %d" % i, "year": 2010, "art": None,
              "missing_total": 2 + i, "seasons": [], "in_progress": True, "yours": 8,
              "genres": ["Comedy"], "rating": 8.0, "source": "tmdb"} for i in range(3)],
    "collections": [{"key": "coll:%d" % i, "name": "Saga %d" % i, "have": 2, "total": 4,
                     "missing": [film(50 + i * 2, "collm"), film(51 + i * 2, "collm")]} for i in range(2)],
    # As the scan writes them: a person's missing films carry no key of their own.
    "directors": [{"key": "dir:1", "name": "Ridley Scott", "owned": 12, "owned_titles": [],
                   "missing": [dict((k, v) for k, v in film(70 + i).items() if k != "key") for i in range(5)]}],
    "actors": [{"key": "act:2", "name": "Florence Pugh", "owned": 4, "owned_titles": [],
                "missing": [dict((k, v) for k, v in film(80 + i).items() if k != "key") for i in range(3)]}],
    "bangers": films,
    "shows": [show(i) for i in range(12)],
    "channels": [],
    "subjects": [{"key": "subject:kw:1", "name": "Heists", "items": [film(200 + i, "subj") for i in range(10)]},
                 {"key": "subject:genre:36", "name": "History", "items": [film(300 + i, "subj") for i in range(6)]}],
}
n.SCAN["result"] = RESULT
n.SCAN["finished_at"] = time.time()

home = n.recs_home()
ids = [r["id"] for r in home["rows"]]
check("rows in order: finish, films, shows, subjects, people",
      ids == ["finish", "films", "shows", "subject:kw:1", "subject:genre:36", "dir:1", "act:2"], ids)
films_row = next(r for r in home["rows"] if r["id"] == "films")
check("eight to a row", len(films_row["items"]) == 8, len(films_row["items"]))
check("each pick carries its reason and three tags",
      all(it.get("why") and len(it.get("tags") or []) == 3 for it in films_row["items"]),
      films_row["items"][0])
keys1 = [it["key"] for it in films_row["items"]]
check("nothing you've hidden", "banger:5" not in keys1, keys1)
check("nothing you own now", "banger:3" not in keys1, keys1)
finish = next(r for r in home["rows"] if r["id"] == "finish")
check("finishing what you have mixes missing episodes and the rest of a series",
      any(it["key"].startswith("show:") for it in finish["items"])
      and any(it["key"].startswith("collm:") for it in finish["items"]), [i["key"] for i in finish["items"]])
check("a missing-episodes pick opens the show you have", all(it.get("show_id") for it in finish["items"]
                                                          if it["key"].startswith("show:")))
check("the people rows say whose", next(r for r in home["rows"] if r["id"] == "dir:1")["title"]
      == "More from Ridley Scott", [r["title"] for r in home["rows"]])

again = n.recs_home()
check("what's dealt stays put until Refresh",
      [it["key"] for it in next(r for r in again["rows"] if r["id"] == "films")["items"]] == keys1)

ref = n.recs_home(refresh=True)
keys2 = [it["key"] for it in next(r for r in ref["rows"] if r["id"] == "films")["items"]]
check("Refresh deals films not shown before", len(keys2) == 8 and not set(keys1) & set(keys2), (keys1, keys2))
# 20 films, less the hidden one and the owned one, is 18: two hands of 8 leave 2.
ref2 = n.recs_home(refresh=True)
row3 = next(r for r in ref2["rows"] if r["id"] == "films")
check("a row that runs dry starts round again, still full", len(row3["items"]) == 8, len(row3["items"]))
check("and says it's running low", row3.get("low"), row3.get("low"))
check("the page knows when it was worked out and how many wait", ref2.get("worked_out") and "waiting" in ref2)

# --- with nothing scanned yet -----------------------------------------------------------
n.SCAN["result"] = None
empty = n.recs_home()
check("nothing scanned yet: no rows, and it says so", empty["rows"] == [] and empty.get("empty"), empty)
n.SCAN["result"] = RESULT

# --- a details page for something you don't own -------------------------------------------
def fake_tmdb(path, params=None, **k):
    if path.startswith("/movie/"):
        return {"id": 900001, "title": "Film 1", "release_date": "2001-05-01", "overview": "A heist.",
                "tagline": "Steal it.", "runtime": 118, "vote_average": 7.6, "vote_count": 1200,
                "genres": [{"id": 80, "name": "Crime"}], "poster_path": "/p.jpg", "backdrop_path": "/b.jpg",
                "credits": {"cast": [{"name": "A Actor", "character": "Thief", "profile_path": "/a.jpg"}],
                            "crew": [{"job": "Director", "name": "D Director"}]},
                "keywords": {"keywords": [{"name": "heist"}]}}
    return {}
n.tmdb = fake_tmdb
d = n.suggestion_detail("900001", "movie")
check("a suggestion's details: plot, cast, who made it, how long, the score",
      d["title"] == "Film 1" and d["overview"] == "A heist." and d["cast"][0]["name"] == "A Actor"
      and d["directors"] == ["D Director"] and d["runtime"] == 118 and d["rating"] == 7.6, d)

# --- the start-up check ------------------------------------------------------------------
ran = {"lib": 0, "recs": 0}
lib_result = {"value": {"movies": 0, "episodes": 0, "unmatched": 0, "removed": 0}}
n.library_scan_worker = lambda: (ran.__setitem__("lib", ran["lib"] + 1),
                                 n.LIBSCAN.update(result=lib_result["value"]))
n.scan_worker = lambda hide_obvious: ran.__setitem__("recs", ran["recs"] + 1)
n.CONFIG["tmdb_key"] = "k"
n.SCAN["finished_at"] = time.time()
n.startup_check()
check("start-up looks at the folders", ran["lib"] == 1, ran)
check("an unchanged library and fresh suggestions: no new scan", ran["recs"] == 0, ran)
lib_result["value"] = {"movies": 2, "episodes": 0, "unmatched": 0, "removed": 0}
n.startup_check()
check("new files: suggestions worked out again", ran["recs"] == 1, ran)
lib_result["value"] = {"movies": 0, "episodes": 0, "unmatched": 0, "removed": 0}
n.SCAN["finished_at"] = time.time() - 8 * 86400
n.startup_check()
check("a week old: worked out again", ran["recs"] == 2, ran)
n.CONFIG["tmdb_key"] = ""
n.startup_check()
check("without a TMDB key there's nothing to work out", ran["recs"] == 2, ran)

# --- the Now chooser: genres combine, and what can't be had is greyed ------------------------
n.LIB.load(force=True)
both = n.build_tonight("film", "any", 0, "Drama,Crime", count=24)
check("two genres at once: everything picked has both",
      both and all(n.genre_matches("Animation", p["genres"] + ["?"]) or True for p in both)
      and all({"Drama", "Crime"} <= set(
          g2 for g in next(m.get("genre") or [] for m in n.LIB.movies if m["movieid"] == p["id"])
          for g2 in n.GENRE_SPLIT.get(g, [g])) for p in both), [p["title"] for p in both][:5])
# The rarest genre on its own leaves most others impossible.
rare = min((g for g in n.available_genres("film", []) if g["n"]), key=lambda g: g["n"])["name"]
avail = dict((g["name"], g["n"]) for g in n.available_genres("film", [rare]))
check("the genres still possible are counted against what's chosen",
      avail.get(rare, 0) > 0 and any(v == 0 for v in avail.values()), (rare, sorted(avail.items())[:8]))
tv = dict((g["name"], g["n"]) for g in n.available_genres("tv", []))
check("TV's doubled genres count as their halves there too",
      "Action & Adventure" not in tv and tv.get("Action", 0) >= 0, sorted(tv)[:10])

# --- the page --------------------------------------------------------------------------
page = n.PAGE
check("the page has the home, Refresh and the suggestion details",
      'id="rechome"' in page and 'id="recrefresh"' in page and "function openSuggestion(" in page
      and "function seeAll(" in page)

check("the PC's Now: Continue on top, the chooser, the pick with its alternatives beside it",
      "body:not(.android) #view-now:not(.hidden){display:grid" in page and 'id="chooserback"' in page
      and "function shortWhy(" in page and "function pcCardOrder(" in page)
check("the chooser: several genres, the impossible greyed, Anything folds it away, and NEXT not NOT THIS",
      "/api/genres" in page and "chosenGenres" in page and "'NEXT'" in page and "'NOT THIS'" not in page)
# 2026-10-25: the arrow beside Anything shows and hides the genres; Film and
# TV bring them out, Anything folds them away.
check("the arrow by Anything shows and hides the genres",
      "genresOpen = !genresOpen" in page and "genresOpen = value !== 'any'" in page
      and "$('#chooserback').onclick = () => $('#spinback').click()" not in page)

# Now's Continue strip: films too. It used to put every half-watched
# episode ahead of every film and stop at six, so with thirty shows on the
# go no film ever showed. Newest first now, films and TV mixed.
n.LIB.loaded_at = 0
cont = n.build_continue()
kinds = set(c["type"] for c in cont)
check("Continue has films as well as TV", {"movie", "episode"} <= kinds, [c["type"] for c in cont][:10])
ats = [c.get("at") or "" for c in cont]
check("newest first", ats == sorted(ats, reverse=True), ats[:6])
check("more than six, since the strip scrolls", len(cont) > 6, len(cont))
check("each says where it's up to", all(c.get("why") for c in cont), [c.get("why") for c in cont][:4])

# The Now page, 2026-10-19: the chooser up beside a shorter Continue, a
# choice that keeps your place, and the wheel scrolling Continue sideways.
page = n.PAGE
check("the chooser and its alternatives stack down the right, beside Continue and the pick",
      'id="nowside"' in page and 'grid-template-areas:"cont side" "pick side"' in page)
check("a choice keeps the chooser where it was on screen",
      "function keepPlace(" in page and "keepPlace(" in page[page.find("async function chooserApply"):][:600])
check("the phone no longer jumps to the top after a choice",
      "$('#view-now').scrollTo({top: 0" not in page)
check("the genre row keeps its sideways place when redrawn",
      "genres.scrollLeft = keepLeft" in page)
check("the wheel scrolls Continue sideways",
      "function wheelSideways(" in page and "wheelSideways($('#unfinished-out'))" in page)

# Settings in tabs, not one long scroll. Every section belongs to a tab.
import re as _re
_settings = page[page.find('<div id="view-settings"'):]
_settings = _settings[:_settings.find('\n<div id="view-', 10) if '\n<div id="view-' in _settings[10:] else 40000]
_cards = _re.findall(r'<div class="settings"[^>]*>', _settings)
check("every Settings section belongs to a tab", _cards and all('data-tab="' in c for c in _cards), _cards)
check("the tabs: Library, Playback, Phone & sharing, Appearance, Storage",
      set(_re.findall(r'data-tab="(\w+)"', _settings)) == {"library", "playback", "sharing", "appearance", "storage"},
      sorted(set(_re.findall(r'data-tab="(\w+)"', _settings))))
check("a tab bar, drawn and remembered", 'id="settabs"' in page and "function showSettingsTab(" in page
      and "nextup.settingsTab" in page)

# 2026-10-19, second pass: no empty chooser on opening. Anything is chosen
# from the start with every tag showing, and tags combine under Anything too.
# 2026-10-25: on the PC they fold away under Anything behind the arrow
# beside it; on the phone they still show from the start.
check("the tags show from the start on the phone", 'class="chooserow genres" id="chooser-genre"' in page
      and "if(!document.body.classList.contains('android')){\n    genres.classList.toggle('hidden', !genresOpen)" in page)
_kind = page[page.find("function chooserKind("):][:700]
check("Anything no longer folds the tags away", "function chooserKind(" in page
      and "chooserStep = 0" not in _kind and "chooserStep = 0" not in page)
check("the tag counts are asked for as the page opens", "drawChooser();\nchooserAvail();" in page)

check("a chosen tag is underlined, as well as filled",
      ".ptag.gchip.on{" in page and "text-decoration:underline" in page[page.find(".ptag.gchip.on{"):][:300])

# The pick's buttons stay put from one pick to the next: they jumped
# between 422 and 487 px as titles wrapped and the line under them grew.
check("the title is one line, fitted to the card", "function fitPickTitle(" in page
      and "fitPickTitle(" in page[page.find("function showPick("):][:600]
      and "body:not(.android) .pick h2{white-space:nowrap" in page
      and "height:48px;line-height:48px" in page)
check("the line under the title is one line", "body:not(.android) .pick .subline{white-space:nowrap" in page)
check("the why line always takes two lines of room", "body:not(.android) .pick .why{" in page
      and "-webkit-line-clamp:2" in page[page.find("body:not(.android) .pick .why{"):][:300])
check("the title's column can narrow, so a one-line title can't push past the card",
      "body:not(.android) .pick > div{min-width:0}" in page)
check("Play is one width, Play or Resume", "body:not(.android) .pick .rowbtns .play{min-width:" in page)

# 2026-10-25: the line above the rating is one angle tied to you, the
# tagline when there's nothing better.
check("genres become words", n._genre_phrase(["Comedy", "War"]) == "war comedy"
      and n._genre_phrase(["Documentary"]) == "documentary" and n._genre_phrase([]) == "")
check("an 8, a 9", n._a_score(8) == "an 8" and n._a_score(8.5) == "an 8.5" and n._a_score(9) == "a 9")
n.LIB.load()
_lines = [n.pick_line("movie", m["movieid"]) for m in n.LIB.movies[:40]]
_lines += [n.pick_line("episode", e["episodeid"]) for e in n.LIB.episodes[:20]]
check("every pick gets a short line", n.LIB.movies and all(isinstance(l, str) and len(l) < 260 for l in _lines)
      and sum(1 for l in _lines if l) >= len(_lines) * 0.8, [l for l in _lines if not l][:3])
check("no stacked keyword lists any more", not any(l.startswith("Shares ") for l in _lines))
_m = n.LIB.movies[0]
_saved = {k: _m.get(k) for k in ("director", "cast_list", "set", "playcount", "rating", "runtime")}
_m.update({"director": [], "cast_list": [], "set": None, "playcount": 0, "rating": 0, "runtime": 0})
_orig_db = n.db
class _Conn:
    def execute(self, *a):
        class C:
            def fetchone(self): return {"tagline": "In space no one can hear you scream."}
        return C()
    def close(self): pass
n.db = lambda: _Conn()
check("nothing better: the tagline", n.pick_line("movie", _m["movieid"]) == "“In space no one can hear you scream.”")
n.db = _orig_db
_m.update(_saved)
_src = open(n.__file__, encoding="utf-8").read()
check("the page is sent it, and the phone gets it from the PC",
      '"cards": build_reasons(kind, ident), "line": line' in _src and 'p["line"] = pick_line(' in _src)
# 2026-10-25: "Rango (2009)" matched a 2009 film with "rango" in its title.
_real_tmdb = n.tmdb
_fake = {
    ("Rango", "2009"): [{"id": 1, "title": "Mentes enfermas de alto rango", "original_title": "Mentes enfermas de alto rango", "release_date": "2009-05-01"}],
    ("Rango", None): [{"id": 2, "title": "Rango", "original_title": "Rango", "release_date": "2011-03-02"},
                      {"id": 1, "title": "Mentes enfermas de alto rango", "release_date": "2009-05-01"}],
    ("Dune", "2021"): [{"id": 3, "title": "Dune", "release_date": "2021-09-15"}],
    ("Dune", None): [{"id": 4, "title": "Dune", "release_date": "1984-12-14"}, {"id": 3, "title": "Dune", "release_date": "2021-09-15"}],
    ("Amelie", "2001"): [{"id": 5, "title": "Amélie", "original_title": "Le Fabuleux Destin d'Amélie Poulain", "release_date": "2001-04-25"}],
    ("Heat", "1995"): [{"id": 6, "title": "Heat", "release_date": "1995-12-15"}],
}
n.tmdb = lambda path, params=None, fresh=False: {"results": _fake.get((params["query"], params.get("year")), [])}
check("a wrong year in the folder doesn't win a wrong film", (n.tmdb_find_movie("Rango", "2009") or {}).get("id") == 2)
check("the right year still picks the remake", (n.tmdb_find_movie("Dune", "2021") or {}).get("id") == 3)
check("accents and the like still match", (n.tmdb_find_movie("Amelie", "2001") or {}).get("id") == 5
      and (n.tmdb_find_movie("Heat", "1995") or {}).get("id") == 6)
check("nothing at all is still nothing", n.tmdb_find_movie("Zzzz", "1999") is None)
n.tmdb = _real_tmdb
check("and shows it", "if(r && r.line){ why.textContent = r.line; return; }" in page
      and "p.line || p.why" in page)

# --- 2026-10-27: the Films tags on Now -------------------------------------------------
_big = {"year": 2019, "budget": 200e6, "revenue": 900e6, "votes": 25000, "rating": 7.9, "genre": ["Action"],
        "keywords": ["explosion"], "set": "Some Saga", "language": "en", "runtime": 160 * 60, "playcount": 0}
_small = {"year": 1975, "budget": 2e6, "revenue": 1e6, "votes": 900, "rating": 7.4, "genre": ["Drama"],
          "keywords": ["twist ending", "based on novel or book"], "set": "", "language": "fr", "runtime": 88 * 60,
          "playcount": 2}
_bt, _st = n.film_tags(_big), n.film_tags(_small)
check("a blockbuster's tags", {"bigbudget", "smash", "crowd", "explosions", "series", "epic", "unseen"} <= _bt
      and not _bt & {"lowbudget", "flop", "classic", "foreign", "short"}, _bt)
check("a small old foreign film's tags", {"classic", "lowbudget", "radar", "cult", "mind", "book", "foreign", "short"} <= _st
      and not _st & {"bigbudget", "smash", "unseen"}, _st)
n.LIB.load()
_av = n.available_film_tags([], [])
check("every tag is offered with a count", [a["key"] for a in _av] == [k for k, _l, _r in n.FILM_TAGS]
      and all(a["n"] >= 0 for a in _av))
_tagged = next((a for a in _av if a["n"] >= 3), None)
_picks = n.build_tonight("film", "any", 0, "", count=12, tags=_tagged["key"]) if _tagged else []
check("a tag keeps Now's picks to films that have it", _tagged and _picks
      and all(p["type"] == "movie" and _tagged["key"] in n.film_tags(next(m for m in n.LIB.movies if m["movieid"] == p["id"]))
              for p in _picks), (_tagged, len(_picks)))
_both = n.available_film_tags([], [_tagged["key"]]) if _tagged else []
check("and the counts narrow with it", _tagged and next(a for a in _both if a["key"] == _tagged["key"])["n"] == _tagged["n"]
      and all(a["n"] <= _tagged["n"] for a in _both))
check("the page has the row, sends the tags, and moves the alternatives under the pick",
      'id="chooser-meta"' in page and "q.set('tags', chosenTags.join(','))" in page
      and "function drawFilmTags()" in page and "view.classList.toggle('withtags', film)" in page)
_src = open(n.__file__, encoding="utf-8").read()
_g0 = [g["name"] for g in n.available_genres("film", [], [])]
_g1 = n.available_genres("film", [_g0[1]], [_tagged["key"]] if _tagged else [])
check("the genre tags keep their places as you choose; the impossible ones grey, never leave",
      _g0 == [g["name"] for g in _g1] and any(g["n"] == 0 for g in _g1))
check("a rated film counts as seen, played here or not",
      n.film_seen({"userrating": 7}) and n.film_seen({"playcount": 1}) and not n.film_seen({})
      and "unseen" not in n.film_tags({"userrating": 8, "playcount": 0}))
check("the phone's PC routes carry the tags", _src.count('tags=one("tags", "")') >= 2
      and 'out["tags"] = available_film_tags(chosen, tags)' in _src)

print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
