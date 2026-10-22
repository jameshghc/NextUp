"""A few seconds isn't a sitting. Flicking through films, or opening one and
closing it again, mustn't leave a resume point, a "last played", or a line in
History. Against a sandbox copy (devserve.isolate)."""
import sys, os, time, tempfile
sys.path.insert(0, r"X:\NextUp"); os.chdir(r"X:\NextUp"); sys.argv = ["nextup.py"]
import nextup as n
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from devserve import isolate
isolate(n, os.path.join(tempfile.gettempdir(), "nextup_shortsit"))

results = []
def check(name, ok, detail=""):
    ok = bool(ok); results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- %s" % (detail,)) if detail != "" else ""))

conn = n.db()
conn.execute("DELETE FROM history")
a, b, c = [r[0] for r in conn.execute("SELECT id FROM movies ORDER BY id LIMIT 3")]
conn.execute("UPDATE movies SET resume_pos=0, resume_total=0, last_played='2026-01-01 20:00:00' WHERE id IN (?,?,?)",
             (a, b, c))
conn.commit(); conn.close()

def row(item_id):
    k = n.db(); r = k.execute("SELECT resume_pos, last_played FROM movies WHERE id=?", (item_id,)).fetchone(); k.close()
    return (r["resume_pos"] or 0, r["last_played"])

def stops(item_id):
    k = n.db()
    got = k.execute("SELECT COUNT(*) FROM history WHERE kind='movie' AND item_id=? AND event IN ('stopped','watched')",
                    (item_id,)).fetchone()[0]
    k.close()
    return got

# --- the PC: started, closed seconds later -------------------------------------------
n.stamp_played("movie", a)
check("starting stamps it as played", row(a)[1] != "2026-01-01 20:00:00", row(a))
n.note_playback_finished("movie", a, 6, position=1206, duration=6000)
check("closed within a minute: no resume point", row(a)[0] == 0, row(a))
check("no 'stopped' in the history", stops(a) == 0, stops(a))
check("and 'last played' goes back to what it was", row(a)[1] == "2026-01-01 20:00:00", row(a))

# A real sitting still counts.
n.stamp_played("movie", b)
n.note_playback_finished("movie", b, 1500, position=1500, duration=6000)
check("a real sitting keeps its resume point", row(b)[0] == 1500, row(b))
check("its stop", stops(b) == 1)
check("and its new 'last played'", row(b)[1] != "2026-01-01 20:00:00", row(b))

# --- History: short sittings and flicks aren't shown ---------------------------------
def at(seconds_ago):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - seconds_ago))
conn = n.db()
conn.execute("DELETE FROM history")
ins = "INSERT INTO history (at,kind,item_id,title,event,seconds,position,total) VALUES (?,?,?,?,?,?,?,?)"
# a: an old-style short stop, already in the table
conn.execute(ins, (at(5000), "movie", a, "A", "played", None, None, None))
conn.execute(ins, (at(4995), "movie", a, "A", "stopped", 5, 5, 6000))
# b: flicked past — started, and another started 20 seconds later
conn.execute(ins, (at(3000), "movie", b, "B", "played", None, None, None))
# c: started 20 seconds after b and watched for half an hour
conn.execute(ins, (at(2980), "movie", c, "C", "played", None, None, None))
conn.execute(ins, (at(1180), "movie", c, "C", "stopped", 1800, 1800, 6000))
conn.commit(); conn.close()
n.LIB.loaded_at = 0
shown = [e["title"] for e in n.build_history(days=1)["items"]]
check("a sitting that lasted seconds isn't in History", "A" not in shown, shown)
check("nor one flicked straight past", "B" not in shown, shown)
check("a real one is", shown and shown[0] == "C" or "C" in shown, shown)

# --- Recently watched only counts real sittings -----------------------------------------
check("Recently watched ignores the history of a flick",
      "'played'" not in open(n.__file__, encoding="utf-8").read().split('if sort == "watched":')[1][:1500])

print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
