"""Queue logic against a COPY of the library, with mpv stubbed out."""
import sys, os, shutil, tempfile, re, subprocess, py_compile
sys.path.insert(0, r"X:\NextUp"); os.chdir(r"X:\NextUp"); sys.argv = ["nextup.py"]
py_compile.compile(r"X:\NextUp\nextup.py", doraise=True)
import nextup as n

here = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(here, "_work")      # scratch output, never committed
os.makedirs(WORK, exist_ok=True)
js = "\n;\n".join(re.findall(r"<script>(.*?)</script>", n.PAGE, re.S))
open(os.path.join(WORK, "page.js"), "w", encoding="utf-8").write(js)
r = subprocess.run(["node", "-e", "new Function(require('fs').readFileSync(process.argv[1],'utf8'));console.log('ok')",
                    os.path.join(WORK, "page.js")], capture_output=True, text=True)
results = []
def check(name, ok, detail=""):
    ok = bool(ok); results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- %s" % (detail,)) if detail != "" else ""))
check("page script parses", r.stdout.strip() == "ok", r.stderr[:300])

# Everything the app can write goes to a sandbox — see devserve.isolate.
sys.path.insert(0, here)
from devserve import isolate
isolate(n, os.path.join(tempfile.gettempdir(), "nextup_queuetest"))
COPY = n.DB_PATH

calls = []
class FakeProc:
    pid = 1
    def poll(self): return None
n.mpv_play = lambda path, start=0, keep_open=False: (calls.append(("play", path, int(start or 0), keep_open)), FakeProc())[1]
n.mpv_command = lambda *a: (calls.append(("cmd",) + a), {"error": "success"})[1]
n.media_file_check = lambda path: True
n.mpv_get = lambda *a, **k: None

n.LIB.load(force=True)
films = sorted(n.LIB.movies, key=lambda m: m["movieid"])[:3]
shows = [s for s in n.LIB.shows if s.get("title") == "Seinfeld"] or n.LIB.shows[:1]
show = shows[0]
n.queue_clear()

# --- adding --------------------------------------------------------------
a = n.queue_add("movie", films[0]["movieid"])
b = n.queue_add("movie", films[1]["movieid"])
c = n.queue_add("tvshow", show["tvshowid"])
d = n.queue_add("tvshow", show["tvshowid"])
st = n.queue_state()
check("four added, in order", [i["title"] for i in st["items"]][:2] == [films[0]["title"], films[1]["title"]] and st["count"] == 4,
      [i["title"] + " " + (i["sub"] or "") for i in st["items"]])
e1, e2 = st["items"][2], st["items"][3]
eps = {e["episodeid"]: e for e in n.LIB.episodes}
o1 = n.episode_order(eps[e1["id"]]); o2 = n.episode_order(eps[e2["id"]])
check("same show twice queues two consecutive episodes, not one twice", e1["id"] != e2["id"] and o2 > o1,
      (e1["sub"], e2["sub"]))
try:
    n.queue_add("movie", films[0]["movieid"]); dup = False
except n.AppError as exc:
    dup = str(exc)
check("the same film twice is refused, with a reason", dup, dup)
nx = n.queue_add("movie", films[2]["movieid"], first=True)
st = n.queue_state()
check("Play next goes to the front", st["items"][0]["id"] == films[2]["movieid"] and nx["position"] == 1)
check("runtimes shown in minutes", 60 <= st["items"][0]["minutes"] <= 300 or st["items"][0]["minutes"] == 0, st["items"][0]["minutes"])

# --- moving / removing ------------------------------------------------------
last = st["items"][-1]["qid"]
st = n.queue_move(last, 0)
check("move last to first", st["items"][0]["qid"] == last)
st = n.queue_remove(last)
check("remove", all(i["qid"] != last for i in st["items"]) and st["count"] == 4)

# --- the hand-over -----------------------------------------------------------
calls.clear()
n.NOW_PLAYING.update(type="movie", id=films[1]["movieid"], title="x", started_at=0,
                     channel=None, channel_id=None, position=6000, duration=6100)
n._PLAY_PROC[0] = FakeProc(); n._KEEP_OPEN[0] = False
n._hold_window_for_queue()
check("a film already playing is switched to hold its window when the queue has items",
      ("cmd", "set_property", "idle", "yes") in calls and n._KEEP_OPEN[0])
head = n.queue_state()["items"][0]
calls.clear()
n._finish_current("ended")
plays = [c for c in calls if c[0] == "play"]
check("film ends -> head of the queue starts", plays and n.NOW_PLAYING["id"] == head["id"],
      (plays, n.NOW_PLAYING.get("title")))
check("and holds its window, because more is queued", plays and plays[0][3] is True)
check("the head left the queue", n.queue_state()["count"] == 3)

calls.clear()
n._finish_current("closed")
check("closing the player does NOT hand over", not [c for c in calls if c[0] == "play"] and n.queue_state()["count"] == 3)

# an episode ending with a queue: queue wins over the next episode
n.NOW_PLAYING.update(type="episode", id=e1["id"], title="x", started_at=0,
                     channel=None, channel_id=None, position=None, duration=None)
head = n.queue_state()["items"][0]
calls.clear()
n._finish_current("ended")
check("episode ends with a queue -> queue, not the next episode",
      n.NOW_PLAYING["id"] == head["id"] and n.NOW_PLAYING["type"] == head["kind"], n.NOW_PLAYING.get("title"))

# a channel ending: the channel carries on, the queue waits
cnt = n.queue_state()["count"]
advanced = []
n.advance_channel = lambda cid, after=None: advanced.append(cid)
n.NOW_PLAYING.update(type="movie", id=films[0]["movieid"], title="x", started_at=0,
                     channel="Comedy #5", channel_id="comedy", position=None, duration=None)
n._KEEP_OPEN[0] = True
n._finish_current("ended")
check("a channel programme ending leaves the queue alone", advanced == ["comedy"] and n.queue_state()["count"] == cnt)

# skipping via play_from_queue while something plays closes the sitting first
n.NOW_PLAYING.update(type="movie", id=films[0]["movieid"], title="x", started_at=0,
                     channel=None, channel_id=None, position=100, duration=6000)
import sqlite3
before = sqlite3.connect(COPY).execute("SELECT COUNT(*) FROM history WHERE event='stopped'").fetchone()[0]
n.play_from_queue()
after = sqlite3.connect(COPY).execute("SELECT COUNT(*) FROM history WHERE event='stopped'").fetchone()[0]
check("skipping to the next closes the outgoing sitting with where it got to", after == before + 1, (before, after))

# empty queue: film ends -> quit, as before
n.queue_clear()
n.NOW_PLAYING.update(type="movie", id=films[0]["movieid"], title="x", started_at=0,
                     channel=None, channel_id=None, position=None, duration=None)
calls.clear()
n._finish_current("ended")
check("empty queue: a film ending closes the window, as before", ("cmd", "quit") in calls and not [c for c in calls if c[0] == "play"])

# a queued file that has gone is skipped, not played as an error
n.queue_add("movie", films[0]["movieid"]); n.queue_add("movie", films[1]["movieid"])
gone = n.LOCAL.path_for("movie", films[0]["movieid"])
n.media_file_check = lambda path: path != gone
n.NOW_PLAYING.update(type=None)
played = n.play_from_queue()
check("a queued file that's gone is dropped and the next one plays", played and played["id"] == films[1]["movieid"])

# persistence
n.queue_add("movie", films[2]["movieid"])
check("queue lives in the database", sqlite3.connect(COPY).execute("SELECT COUNT(*) FROM queue").fetchone()[0] == 1)

print("\n%d/%d passed" % (sum(results), len(results)))
