import os, sys, shutil, tempfile
from collections import defaultdict, Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import devserve, nextup as n
box = os.path.join(tempfile.gettempdir(), "nextup_recentep")
devserve.isolate(n, box)
shutil.copytree(r"X:\NextUp\nextup_resume", n.WATCH_LATER, dirs_exist_ok=True)
n.LIB.load(force=True)
by_show = defaultdict(list)
for e in n.LIB.episodes: by_show[e.get("tvshowid")].append(e)

def old_progress(tid):
    eps = sorted([e for e in by_show.get(tid) or [] if (e.get("season") or 0) > 0], key=n.episode_order)
    part = [e for e in eps if (e.get("resume") or {}).get("position")]
    if part: return ("resume", part[-1])
    fin = [e for e in eps if e.get("playcount")]
    if not fin: return None
    last = max(fin, key=n.episode_order)
    fol = [e for e in eps if n.episode_order(e) > n.episode_order(last)]
    return ("next", fol[0]) if fol else None

code = lambda e: "S%02dE%02d" % (e.get("season") or 0, e.get("episode") or 0)
changed = 0
for s in sorted(n.LIB.shows, key=lambda s: s.get("title") or ""):
    tid = s.get("tvshowid"); o = old_progress(tid); p = n.series_progress(by_show, tid)
    new = (p["state"], p["episode"]) if p else None
    if (o and (o[0], code(o[1]))) != (new and (new[0], code(new[1]))):
        changed += 1
        latest = max((e for e in by_show[tid] if e.get("last_played")), key=lambda e: e["last_played"], default=None)
        print("%-34s old %-16s new %-16s  last watched %s" % ((s.get("title") or "")[:34],
              o and "%s %s" % (o[0], code(o[1])), new and "%s %s" % (new[0], code(new[1])),
              latest and "%s at %s" % (code(latest), latest["last_played"][5:16])))
print("\n%d shows changed of %d" % (changed, len(n.LIB.shows)))

row = [i for i in n.build_resume_row(limit=None) if i["type"] == "episode"][:3]
print("\nTV resume tile, newest first:", [(i["title"], i["sub"], i["note"], i["at"][5:16]) for i in row])

picks = Counter()
seen = defaultdict(set)
for _ in range(400):
    for p in n.build_tonight("tv", "any", 0, "", count=3):
        picks[p["title"]] += 1; seen[p["title"]].add(p["sub"].split(" · ")[0])
favs = {s["title"] for s in n.LIB.shows if s.get("favourited")}
print("\nNow tab, 400 draws of 3:")
for t, c in picks.most_common(12):
    print("  %-34s offered %3d  distinct episodes %3d  %s" % (t[:34], c, len(seen[t]), "FAV" if t in favs else ""))
sample = [p for p in n.build_tonight("tv", "any", 0, "", count=3)]
print("\nwhy lines:", [(p["title"], p["why"]) for p in sample])
