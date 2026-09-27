"""Measure "Pick something" fairness. Works on whatever the algorithm
currently is: odds come from sampling the real weighted_sample, so it
survives changes to the pools inside it.

Usage: pick_audit_v2.py <label>   — writes <label>.json for comparison.
"""
import sys, os, tempfile, random, json, collections, statistics, time
sys.path.insert(0, r"X:\NextUp"); os.chdir(r"X:\NextUp"); sys.argv = ["nextup.py"]
import nextup as n
here = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(here, "_work")      # scratch output, never committed
os.makedirs(WORK, exist_ok=True)
sys.path.insert(0, here)
from devserve import isolate
isolate(n, os.path.join(tempfile.gettempdir(), "nextup_pickaudit_v2"))

LABEL = sys.argv[1] if len(sys.argv) > 1 else "run"
ARGS = dict(kind="any", mood="any", max_mins=0, genre="")
DRAWS = 40000
PRESSES = 3000
n.LIB.load(force=True)

cap = {}
real_ws = n.weighted_sample
n.weighted_sample = lambda items, k: (cap.__setitem__("items", items), real_ws(items, k))[1]
n.build_tonight(exclude=set(), **ARGS)
n.weighted_sample = real_ws
items = cap["items"]
key = lambda p: "%s:%s" % (p["type"], p["id"])
label = lambda p: p["title"] + (" (TV)" if p["type"] == "episode" else "")

# what each title IS, for grouping
info = {}
for p in items:
    ongoing = p["type"] == "episode" and ("got to" in p["why"] or "pick it back up" in p["why"])
    info[key(p)] = {"title": label(p), "tv": p["type"] == "episode",
                    "rated": bool(p.get("userrating")), "ongoing": ongoing,
                    "watchlisted": bool(p.get("watchlisted")), "tmdb": p["rating"]}

print("=" * 78)
print("%s — %d eligible (%d films, %d shows)" % (LABEL, len(items),
      sum(1 for i in info.values() if not i["tv"]), sum(1 for i in info.values() if i["tv"])))
print("=" * 78)

random.seed(11)
hits = collections.Counter()
t0 = time.time()
for _ in range(DRAWS):
    got = real_ws(items, 1)
    if got:
        hits[key(got[0])] += 1
print("odds from %d draws in %.0fs" % (DRAWS, time.time() - t0))
odds = {k: c / float(DRAWS) for k, c in hits.items()}
uniform = 1.0 / len(items)

def group(name, pred):
    members = [k for k, i in info.items() if pred(i)]
    if not members:
        return
    share = sum(odds.get(k, 0) for k in members)
    print("  %-46s %4d titles  %5.1f%% of presses   each 1 in %5.0f" % (
        name, len(members), 100 * share, (len(members) / share) if share else 99999))

group("films", lambda i: not i["tv"])
group("  unrated films", lambda i: not i["tv"] and not i["rated"])
group("  rated films", lambda i: not i["tv"] and i["rated"])
group("shows", lambda i: i["tv"])
group("  shows you're part way through", lambda i: i["tv"] and i["ongoing"])
group("  other shows", lambda i: i["tv"] and not i["ongoing"])
group("watchlisted", lambda i: i["watchlisted"])
group("TMDB 8.0+", lambda i: i["tmdb"] >= 8.0)
group("TMDB 7.0-7.9", lambda i: 7.0 <= i["tmdb"] < 8.0)
group("TMDB under 7.0 (rated titles)", lambda i: 0 < i["tmdb"] < 7.0)

ranked = sorted(info, key=lambda k: -odds.get(k, 0))
print("\n  most likely:")
for k in ranked[:10]:
    print("    %5.1fx fair  1 in %4.0f  %s" % (odds.get(k, 0) / uniform, 1 / odds[k] if odds.get(k) else 0, info[k]["title"]))
inpool = [odds.get(k, 0) / uniform for k in info]
print("\n  top 10%% of titles take %.0f%% of presses; %d titles never drawn in %d" % (
      100 * sum(sorted(odds.values(), reverse=True)[:int(len(items) * .1)]),
      len(items) - len(hits), DRAWS))
print("  likeliest : least likely = %.0fx" % (max(inpool) / min(x for x in inpool if x > 0)) if min(inpool) > 0 else "")

# --- real presses with the cooldown -----------------------------------------
conn = n.db(); conn.execute("DELETE FROM offered"); conn.commit(); conn.close()
random.seed(7)
shown, session = [], set()
t0 = time.time()
for i in range(PRESSES):
    if i % 12 == 0:
        session = set()
    picks = n.picks_with_cooldown(set(session), ARGS) or n.build_tonight(**ARGS)
    k = key(picks[0])
    n.remember_offer(k)
    session.add(k)
    shown.append(k)
counts = collections.Counter(shown)
fair = PRESSES / float(len(items))
print("\n  %d presses in %.0fs: %d distinct titles, %d never shown" % (
      PRESSES, time.time() - t0, len(counts), len(items) - len(counts)))
print("  per title: median %s, max %d (%.1fx fair share of %.1f)" % (
      statistics.median([counts.get(k, 0) for k in info]), max(counts.values()),
      max(counts.values()) / fair, fair))
tvp = sum(c for k, c in counts.items() if k.startswith("episode:"))
ongoing = sum(c for k, c in counts.items() if info.get(k, {}).get("ongoing"))
print("  shows: %.0f%% of presses (%.0f%% of titles); shows you're part way through: %.0f%%" % (
      100 * tvp / PRESSES, 100 * sum(1 for i in info.values() if i["tv"]) / len(info), 100 * ongoing / PRESSES))
print("  most frequent: " + ", ".join("%s x%d" % (info[k]["title"], c) for k, c in counts.most_common(6)))
gaps, last = [], {}
for i, k in enumerate(shown):
    if k in last:
        gaps.append(i - last[k])
    last[k] = i
showgaps, lastshow = [], {}
for i, k in enumerate(shown):
    if k.startswith("episode:"):
        sid = info[k]["title"]
        if sid in lastshow:
            showgaps.append(i - lastshow[sid])
        lastshow[sid] = i
if gaps:
    print("  same title again after: min %d presses, median %d" % (min(gaps), statistics.median(gaps)))
if showgaps:
    print("  same SHOW again after:  min %d presses, median %d" % (min(showgaps), statistics.median(showgaps)))

json.dump({"label": LABEL, "odds": odds, "counts": counts.most_common(), "info": info},
          open(os.path.join(WORK, "audit_%s.json" % LABEL), "w"), indent=1)
