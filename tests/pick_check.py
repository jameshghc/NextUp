"""Two specifics: is the show cooldown actually holding, and where do
watchlisted films sit in the ranking now?"""
import sys, os, tempfile, random, collections, statistics
sys.path.insert(0, r"X:\NextUp"); os.chdir(r"X:\NextUp"); sys.argv = ["nextup.py"]
import nextup as n
here = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(here, "_work")      # scratch output, never committed
os.makedirs(WORK, exist_ok=True)
sys.path.insert(0, here)
from devserve import isolate
isolate(n, os.path.join(tempfile.gettempdir(), "nextup_pickcheck"))
n.LIB.load(force=True)
ARGS = dict(kind="any", mood="any", max_mins=0, genre="")

conn = n.db(); conn.execute("DELETE FROM offered"); conn.commit(); conn.close()
random.seed(3)
show_of = dict((e.get("episodeid"), e.get("tvshowid")) for e in n.LIB.episodes)
title_of = dict((s.get("tvshowid"), s.get("title")) for s in n.LIB.shows)
seq = []
for i in range(600):
    picks = n.picks_with_cooldown(set(), ARGS)
    p = picks[0]
    n.remember_offer("%s:%s" % (p["type"], p["id"]))
    seq.append((p["type"], p["id"]))

gaps_by_showid, last = [], {}
offenders = []
for i, (t, pid) in enumerate(seq):
    if t != "episode":
        continue
    sid = show_of.get(pid)
    if sid in last:
        gap = i - last[sid]
        gaps_by_showid.append(gap)
        if gap < n.SHOW_COOLDOWN:
            offenders.append((title_of.get(sid), sid, gap))
    last[sid] = i
print("SHOW COOLDOWN = %d presses" % n.SHOW_COOLDOWN)
print("  same show id again after: min %d, median %d (%d repeats over 600 presses)" % (
      min(gaps_by_showid), statistics.median(gaps_by_showid), len(gaps_by_showid)))
print("  breaches (gap < cooldown):", offenders[:6] or "none")

# by TITLE, which is how it looks to a person
gaps_by_title, lastt = [], {}
bad = []
for i, (t, pid) in enumerate(seq):
    if t != "episode":
        continue
    name = title_of.get(show_of.get(pid))
    if name in lastt:
        g = i - lastt[name]
        gaps_by_title.append(g)
        if g < n.SHOW_COOLDOWN:
            bad.append((name, g))
    lastt[name] = i
print("  same show TITLE again after: min %d (%s)" % (min(gaps_by_title), bad[:4] or "none"))
dupes = collections.Counter(title_of.values())
print("  shows sharing a title in the library:", [t for t, c in dupes.items() if c > 1] or "none")

# where watchlisted films sit
cap = {}
real = n.weighted_sample
n.weighted_sample = lambda items, k: (cap.__setitem__("items", items), real(items, k))[1]
n.build_tonight(exclude=set(), **ARGS)
n.weighted_sample = real
items = cap["items"]
main = sorted([p for p in items if not p.get("rewatch")], key=lambda p: -p["score"])
films = [p for p in main if p["type"] == "movie"]
wl = [i for i, p in enumerate(films) if p.get("watchlisted")]
print("\nWATCHLIST, among the %d films in the main draw:" % len(films))
print("  watchlisted films sit at positions:", wl[:14])
print("  top 12 films in the draw:")
for p in films[:12]:
    print("    %-44s TMDB %.1f%s" % (p["title"][:44], p["rating"], "  [watchlist]" if p.get("watchlisted") else ""))
print("\n  top 8 shows in the draw:")
for p in [p for p in main if p["type"] == "episode"][:8]:
    print("    %-30s %s" % (p["title"][:30], p["why"][:70]))
