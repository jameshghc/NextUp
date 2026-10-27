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

# --- Quitting the app mid-episode (2026-10-25) ----------------------------------------------
# Cyberpunk S1E4, stopped at 12:54 when the app was quit to restart it: the
# stop was seen and recorded, mpv left no resume file of its own, and the
# next start took "no file" as "watched to the end" — Continue said S1E5.
conn = n.db()
ep_a, ep_b = [r[0] for r in conn.execute("SELECT id FROM episodes ORDER BY id LIMIT 2")]
conn.execute("UPDATE episodes SET resume_pos=774, resume_total=1532, playcount=0 WHERE id IN (?,?)", (ep_a, ep_b))
conn.execute("DELETE FROM history WHERE kind='episode' AND item_id IN (?,?)", (ep_a, ep_b))
ins = "INSERT INTO history (at,kind,item_id,title,event,seconds,position,total) VALUES (?,?,?,?,?,?,?,?)"
conn.execute(ins, (at(900), "episode", ep_a, "A", "played", None, None, None))
conn.execute(ins, (at(100), "episode", ep_a, "A", "stopped", 774, 774, 1532))     # seen to stop here
conn.execute(ins, (at(900), "episode", ep_b, "B", "played", None, None, None))    # never seen to end
conn.commit(); conn.close()
_real_points = n.read_resume_points
n.read_resume_points = lambda: {}          # mpv's folder is readable, and has nothing for either
n.sync_playback_state()
n.read_resume_points = _real_points
conn = n.db()
ra = conn.execute("SELECT resume_pos, playcount FROM episodes WHERE id=?", (ep_a,)).fetchone()
rb = conn.execute("SELECT resume_pos, playcount FROM episodes WHERE id=?", (ep_b,)).fetchone()
conn.close()
check("a stop the app saw keeps its place through a restart", ra["resume_pos"] == 774 and not ra["playcount"],
      tuple(ra))
check("one it never saw end is still read as finished, as before", rb["resume_pos"] == 0 and rb["playcount"] == 1,
      tuple(rb))

# --- 2026-10-25: flicking past on a channel ----------------------------------------
# Changing channel had mpv save the outgoing film's place, and Continue showed
# films that were only on for seconds, which History didn't list.
k = n.db()
d, e2 = [r[0] for r in k.execute("SELECT id FROM movies ORDER BY id LIMIT 2 OFFSET 5")]
k.execute("UPDATE movies SET resume_pos=1500, resume_total=6000 WHERE id=?", (d,))
k.execute("UPDATE movies SET resume_pos=0, resume_total=0 WHERE id=?", (e2,))
k.commit(); k.close()
n.stamp_played("movie", d)
k = n.db(); k.execute("UPDATE movies SET resume_pos=4200 WHERE id=?", (d,)); k.commit(); k.close()   # mpv's save, folded in
n.note_playback_finished("movie", d, 8, position=4210, duration=6000)
check("a flick puts the place back where it was before", row(d)[0] == 1500, row(d))
n.stamp_played("movie", e2)
k = n.db(); k.execute("UPDATE movies SET resume_pos=4200 WHERE id=?", (e2,)); k.commit(); k.close()
n.note_playback_finished("movie", e2, 8, position=4210, duration=6000)
check("and one with no place before has none after", row(e2)[0] == 0, row(e2))

k = n.db()
k.execute("UPDATE movies SET resume_pos=4200, resume_total=6000, last_played=? WHERE id=?", (n.now_stamp(), e2))
_p = k.execute("SELECT path FROM movies WHERE id=?", (e2,)).fetchone()[0]
k.commit(); k.close()
n._sync_watch_later(_p, 4200)        # mpv's own file, as a real one leaves
n.log_event("movie", e2, "x", "tuned in via Comedy #5")
n.LIB.loaded_at = 0
check("Continue skips what was only tuned into", not any(c["type"] == "movie" and c["id"] == e2
                                                         for c in n.build_resume_row(limit=0)))
n.log_event("movie", e2, "x", "stopped", seconds=1800, position=4200, total=6000)
n.LIB.loaded_at = 0
check("but not a real stretch on a channel", any(c["type"] == "movie" and c["id"] == e2
                                                 for c in n.build_resume_row(limit=0)))
_src = open(n.__file__, encoding="utf-8").read()
check("an outgoing flick isn't saved by mpv at all",
      'reason == "skipped" and current.get("type") in ("movie", "episode")' in _src
      and "and time.time() - (current.get(\"started_at\") or time.time()) >= MIN_WATCH_SECONDS):\n        mpv_command(\"write-watch-later-config\")" in _src)
check("anything put into an open window closes the sitting before it",
      _src.count("_close_outgoing()") >= 3 and "if mpv_alive():\n        _close_outgoing()" in _src)

# Before "stopped" was written for a channel: the gap before the next thing
# says whether it was a flick (seconds) or a sitting (nine minutes).
k = n.db()
f1, f2 = [r[0] for r in k.execute("SELECT id FROM movies ORDER BY id LIMIT 2 OFFSET 8")]
for fid in (f1, f2):
    k.execute("UPDATE movies SET resume_pos=4200, resume_total=6000, last_played=? WHERE id=?", (n.now_stamp(), fid))
    n._sync_watch_later(k.execute("SELECT path FROM movies WHERE id=?", (fid,)).fetchone()[0], 4200)
k.execute("INSERT INTO history (at, kind, item_id, title, event) VALUES ('2030-01-01 03:18:10','movie',?,'a','tuned in via X #1')", (f1,))
k.execute("INSERT INTO history (at, kind, item_id, title, event) VALUES ('2030-01-01 03:18:19','movie',?,'b','tuned in via X #2')", (f2,))
k.execute("INSERT INTO history (at, kind, item_id, title, event) VALUES ('2030-01-01 03:27:34','episode',1,'c','played')")
k.commit(); k.close()
n.LIB.loaded_at = 0
_ids = {c["id"] for c in n.build_resume_row(limit=0) if c["type"] == "movie"}
check("nine seconds on before the next channel: a flick", f1 not in _ids)
check("nine minutes on before the next thing: a sitting", f2 in _ids)

# 2026-10-27: the Library's Recently watched goes by real sittings too.
k = n.db()
g1, g2 = [r[0] for r in k.execute("SELECT id FROM movies ORDER BY id LIMIT 2 OFFSET 12")]
k.execute("INSERT INTO history (at, kind, item_id, title, event) VALUES ('2031-01-01 20:00:00','movie',?,'flick','tuned in via X #1')", (g1,))
k.execute("INSERT INTO history (at, kind, item_id, title, event) VALUES ('2031-01-01 20:00:05','movie',?,'sat','played')", (g2,))
k.execute("INSERT INTO history (at, kind, item_id, title, event, seconds, position, total)"
          " VALUES ('2031-01-01 20:40:00','movie',?,'sat','stopped',2395,2400,6000)", (g2,))
k.execute("UPDATE movies SET last_played='2031-01-01 20:00:00' WHERE id=?", (g1,))
k.commit(); k.close()
n.LIB.loaded_at = 0
sat = n.real_sittings()
check("a flick isn't a sitting, forty minutes is", ("movie", g1) not in sat and sat.get(("movie", g2)) == "2031-01-01 20:40:00")
top = n.browse_library("film", "", "watched", "all", 3, 0)["items"]
check("Recently watched: the forty minutes first, not the flick", top and top[0]["id"] == g2
      and all(r["id"] != g1 for r in top), [r["title"] for r in top])

# 2026-10-27: History leaves out an unclosed start followed within a minute by
# anything else — a channel tune-in too, not only another play.
k = n.db()
h1, h2, h3 = [r[0] for r in k.execute("SELECT id FROM movies ORDER BY id LIMIT 3 OFFSET 20")]
_now = time.time()
_at = lambda s: time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(_now - s))
k.execute("INSERT INTO history (at, kind, item_id, title, event) VALUES (?,'movie',?,'flicked','played')", (_at(3600), h1))
k.execute("INSERT INTO history (at, kind, item_id, title, event) VALUES (?,'movie',?,'next','tuned in via X #1')", (_at(3590), h2))
k.execute("INSERT INTO history (at, kind, item_id, title, event) VALUES (?,'movie',?,'kept','played')", (_at(1800), h3))
k.execute("INSERT INTO history (at, kind, item_id, title, event) VALUES (?,'movie',?,'after','tuned in via X #2')", (_at(1500), h2))
k.execute("UPDATE movies SET last_played=? WHERE id=?", (_at(1800), h3))     # as a real start stamps it
k.commit(); k.close()
n.LIB.loaded_at = 0
_hist = n.build_history(days=2)
_ids = {(i.get("kind"), i.get("id")) for i in _hist["items"]}
_shown = lambda mid: any(str(mid) == str(i.get("id")) and i.get("kind") in ("movie", None) for i in _hist["items"]) \
    or ("movie", mid) in _ids
check("History: ten seconds then a channel tuned in isn't shown", not _shown(h1), [(i.get("title"), i.get("id")) for i in _hist["items"]][:6])
check("five minutes then something else is", _shown(h3))

# History's bar is two minutes, and three more ways to tell a short one.
k = n.db()
j1, j2, j3 = [r[0] for r in k.execute("SELECT id FROM movies ORDER BY id LIMIT 3 OFFSET 30")]
k.execute("INSERT INTO history (at, kind, item_id, title, event, seconds, position, total)"
          " VALUES (?,'movie',?,'81 seconds','stopped',81,2382,8353)", (_at(900), j1))
k.execute("INSERT INTO history (at, kind, item_id, title, event, seconds, position, total)"
          " VALUES (?,'movie',?,'asleep','stopped',980,78,1273)", (_at(800), j2))
k.execute("INSERT INTO history (at, kind, item_id, title, event) VALUES (?,'movie',?,'closed fast','played')", (_at(60), j3))
k.execute("UPDATE movies SET last_played='2026-09-18 03:24:36' WHERE id=?", (j3,))      # put back, as unstamp does
k.commit(); k.close()
n.LIB.loaded_at = 0
_hist = n.build_history(days=2)
_ids = {(i.get("kind"), i.get("id")) for i in _hist["items"]}
check("History: 81 seconds isn't shown (under two minutes)", ("movie", j1) not in _ids)
check("nor sixteen minutes open but only 78 seconds into it", ("movie", j2) not in _ids)
check("nor a start whose 'last played' was put back (closed within moments)", ("movie", j3) not in _ids)

print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
