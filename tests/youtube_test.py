"""A YouTube channel (Cold Ones) end to end, with a FAKE yt-dlp and mpv
stubbed out, so nothing here touches the internet or opens a player.

The fake prints a channel page the way `yt-dlp --flat-playlist -J` does,
including the things that must be left out: a short, an upcoming premiere
with no length, and a live stream."""
import sys, os, json, time, tempfile, re, subprocess
sys.path.insert(0, r"X:\NextUp"); os.chdir(r"X:\NextUp"); sys.argv = ["nextup.py"]
import nextup as n
here = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(here, "_work")
os.makedirs(WORK, exist_ok=True)
sys.path.insert(0, here)
from devserve import isolate
isolate(n, os.path.join(tempfile.gettempdir(), "nextup_youtubetest"))

results = []
def check(name, ok, detail=""):
    ok = bool(ok); results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- %s" % (detail,)) if detail != "" else ""))

# Start from no saved list at all, whatever the copy brought with it.
if os.path.exists(n.YOUTUBE_PATH):
    os.remove(n.YOUTUBE_PATH)

# --- the fake yt-dlp ----------------------------------------------------------
REAL = [{"id": "vid%02d" % i, "title": "Cold Ones video %d" % i,
         "duration": 1200 + 60 * i} for i in range(12)]
page = {"channel": "Cold Ones", "entries": REAL + [
    {"id": "short01", "title": "A Short", "duration": 45},
    {"id": "soon01", "title": "Premiere tomorrow", "duration": None,
     "live_status": "is_upcoming"},
    {"id": "live01", "title": "Live now", "duration": 5000, "live_status": "is_live"},
]}
fake_py = os.path.join(WORK, "fake_ytdlp.py")
fake_json = os.path.join(WORK, "fake_ytdlp_page.json")
json.dump(page, open(fake_json, "w", encoding="utf-8"))
open(fake_py, "w", encoding="utf-8").write(
    "import sys, os\n"
    "if os.path.exists(os.path.join(os.path.dirname(__file__), 'fake_ytdlp_FAIL')):\n"
    "    sys.stderr.write('ERROR: Unable to download webpage: offline\\n'); sys.exit(1)\n"
    "sys.stdout.write(open(os.path.join(os.path.dirname(__file__), 'fake_ytdlp_page.json'), encoding='utf-8').read())\n")
fake_bat = os.path.join(WORK, "fake_ytdlp.bat")
open(fake_bat, "w").write('@"%s" "%s" %%*\n' % (sys.executable, fake_py))
FAIL_FLAG = os.path.join(WORK, "fake_ytdlp_FAIL")
if os.path.exists(FAIL_FLAG):
    os.remove(FAIL_FLAG)
n.find_ytdlp = lambda: fake_bat

# --- mpv, stubbed ---------------------------------------------------------------
calls = []
class FakeProc:
    pid = 1
    def poll(self): return None
n.mpv_play = lambda path, start=0, keep_open=False: (calls.append((path, int(start or 0), keep_open)), FakeProc())[1]
n.mpv_command = lambda *a: {"error": "success"}
n.mpv_get = lambda *a, **k: None
n.raise_app_window = lambda: None

check("Cold Ones is off the dial", not any(c["id"] == "coldones" for c in n.CHANNELS))
check("Al Jazeera is the last channel", n.CHANNELS[-1]["id"] == "news" and n.CHANNELS[-1]["number"] == 22,
      n.CHANNELS[-1]["name"])
# Favourites in two: films on one, shows on the other, side by side.
_ids = [c["id"] for c in n.CHANNELS]
_ff, _ft = (next(c for c in n.CHANNELS if c["id"] == i) for i in ("favs", "favstv"))
check("Non-stop Favs is two channels, films then TV, side by side",
      _ff.get("film_only") and _ft.get("tv_only") and _ids.index("favstv") == _ids.index("favs") + 1,
      (_ff["name"], _ft["name"]))
n.LIB.movies = [{"movieid": 1, "title": "Fav Film", "favourited": True, "runtime": 100, "file": "f.mkv"}]
n.LIB.shows = [{"tvshowid": 2, "title": "Fav Show", "favourited": True}]
n.LIB.episodes = [{"episodeid": 3, "tvshowid": 2, "season": 1, "episode": 1, "runtime": 30, "title": "Pilot",
                   "file": "e.mkv"}]
_kf = {b["kind"] for b in n.channel_blocks(_ff)}
_kt = {b["kind"] for b in n.channel_blocks(_ft)}
check("films only on the films one, episodes only on the TV one", _kf == {"movie"} and _kt == {"episodes"},
      (_kf, _kt))
n.LIB.loaded_at = 0
# The YouTube channel type stays: tested on a channel of its own, added here.
n.CHANNELS.append({"id": "coldones", "name": "Cold Ones #22", "number": 22, "type": "youtube",
                   "source": "https://www.youtube.com/@ColdOnes/videos"})
ch = n.CHANNELS[-1]
check("channels 2 to 5 are films only",
      all(c.get("film_only") for c in n.CHANNELS[1:5]), [(c["name"], c.get("film_only")) for c in n.CHANNELS[1:5]])

def wait_fetch():
    for _ in range(300):
        with n._YT_LOCK:
            if ch["id"] not in n._YT_FETCHING:
                return True
        time.sleep(0.05)
    return False

# --- first look: nothing saved, so it fetches in the background ------------------
t = time.time()
first = n.channel_blocks(ch)
quick = time.time() - t
check("with nothing saved, the schedule doesn't wait on YouTube", first == [] and quick < 1, "%.2fs" % quick)
note = n.youtube_status(ch)
check("and the card says it's fetching", "Getting the video list" in note, note)
check("the fetch finishes", wait_fetch())
blocks = n.channel_blocks(ch)
ids = [b["id"] for b in blocks]
check("all twelve real videos, and not the short, the premiere or the live stream",
      sorted(ids) == sorted(v["id"] for v in REAL), ids)
check("each block has its length, a thumbnail and a title",
      all(b["duration"] >= 1200 and b["art"].startswith("https://i.ytimg.com/vi/") and b["title"] for b in blocks))
check("in a shuffled order, not the page's", ids != sorted(ids), ids)
check("the same order every time", [b["id"] for b in n.channel_blocks(ch)] == ids)

# --- the Channels page --------------------------------------------------------
now = n.resolve_all_channels_now().get("coldones")
check("something is on", now and now["block"]["kind"] == "youtube", now and now["block"]["title"])
summary = n.channel_summary(now)
check("the card shows it like any programme",
      summary["title"].startswith("Cold Ones video") and summary["duration"] > 0
      and summary["next_title"] != summary["title"], summary)

# --- tuning in --------------------------------------------------------------------
calls.clear()
n.tune_channel(ch)
url, start, keep_open = calls[-1]
on = n.resolve_all_channels_now()["coldones"]
check("tuning in opens the video's YouTube address, holding the window",
      url == n.youtube_url(on["block"]["id"]) and keep_open, calls[-1])
check("part way in, where the schedule says", abs(start - int(on["offset"])) <= 3,
      (start, int(on["offset"])))
p = n.now_playing_snapshot()
check("the playing bar knows what it is", p and p["type"] == "youtube"
      and p["title"] == on["block"]["title"] and p["sub"] == "Cold Ones"
      and p["art"] == n.youtube_thumb(on["block"]["id"]) and p["channel_id"] == "coldones", p)
conn = n.db()
last = conn.execute("SELECT kind,title,event FROM history ORDER BY id DESC LIMIT 1").fetchone()
conn.close()
check("History has the tune-in", tuple(last) == ("youtube", on["block"]["title"], "tuned in via Cold Ones #22"),
      tuple(last))

# --- the video ends: the next one comes on, from the start ------------------------------
playing_id = p["id"]
n._KEEP_OPEN[0] = True
n.afk_should_ask = lambda: False
calls.clear()
with n._PLAY_LOCK:                           # played through to the end
    n.NOW_PLAYING.update(position=on["block"]["duration"], duration=on["block"]["duration"])
n._finish_current("ended")
check("when it ends, another video comes on", calls and calls[-1][0] != n.youtube_url(playing_id), calls)
check("from its beginning", calls and calls[-1][1] == 0, calls)
p2 = n.now_playing_snapshot()
conn = n.db()
last = conn.execute("SELECT event FROM history ORDER BY id DESC LIMIT 1").fetchone()[0]
conn.close()
check("logged as next up on the channel", p2 and p2["type"] == "youtube" and last == "next up on Cold Ones #22",
      (p2 and p2["title"], last))

# --- refused, not ended: stop rather than race through the channel -------------------
quits = []
n.mpv_command = lambda *a: (quits.append(a), {"error": "success"})[1]
calls.clear()
with n._PLAY_LOCK:
    n.NOW_PLAYING.update(position=None)      # it never got going
n._finish_current("ended")
check("a video that never played doesn't hand on to the next", not calls, calls)
check("it closes the window and flags it", ("quit",) in quits and n.YT_PLAY_FAILED["at"] > 0, quits)
n.mpv_command = lambda *a: {"error": "success"}

# --- offline: yesterday's list stays ----------------------------------------------
open(FAIL_FLAG, "w").close()
cache = json.load(open(n.YOUTUBE_PATH, encoding="utf-8"))
cache["coldones"]["fetched_at"] = 0        # due a refresh
cache["coldones"]["tried_at"] = 0
json.dump(cache, open(n.YOUTUBE_PATH, "w", encoding="utf-8"))
n.channel_blocks(ch)
wait_fetch()
entry = json.load(open(n.YOUTUBE_PATH, encoding="utf-8"))["coldones"]
check("a failed refresh keeps the list it had", len(entry.get("videos") or []) == 12, len(entry.get("videos") or []))
check("and says why", "offline" in (entry.get("error") or ""), entry.get("error"))
before = entry["tried_at"]
n.channel_blocks(ch)
time.sleep(0.3)
entry = json.load(open(n.YOUTUBE_PATH, encoding="utf-8"))["coldones"]
check("and doesn't try again straight away", entry["tried_at"] == before)
os.remove(FAIL_FLAG)

# --- no yt-dlp at all --------------------------------------------------------------
n.find_ytdlp = lambda: None
try:
    n.youtube_fetch(ch["source"]); missing = None
except n.AppError as exc:
    missing = str(exc)
check("without yt-dlp, it says how to install it", missing and "winget install yt-dlp" in missing, missing)
try:
    n.youtube_play("vid01"); refused = None
except n.AppError as exc:
    refused = str(exc)
check("and won't try to play", refused and "yt-dlp" in refused, refused)

# --- the page draws it ---------------------------------------------------------------
js = "\n;\n".join(re.findall(r"<script>(.*?)</script>", n.PAGE, re.S))
open(os.path.join(WORK, "page.js"), "w", encoding="utf-8").write(js)
r = subprocess.run(["node", "-e", "new Function(require('fs').readFileSync(process.argv[1],'utf8'));console.log('ok')",
                    os.path.join(WORK, "page.js")], capture_output=True, text=True)
check("page script parses", r.stdout.strip() == "ok", r.stderr[:300])

print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
