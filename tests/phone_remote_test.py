"""The phone as a remote for the PC: one set of remote actions shared by the
desktop remote and the phone, the routes the paired phone reaches over the
Wi-Fi, the phone's passthrough, and the page. mpv is faked; everything runs
against a sandbox copy (devserve.isolate) on loopback ports 8791/8792."""
import sys, os, re, json, time, tempfile, threading, urllib.request, urllib.error
sys.path.insert(0, r"X:\NextUp"); os.chdir(r"X:\NextUp"); sys.argv = ["nextup.py"]
import nextup as n
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from devserve import isolate
isolate(n, os.path.join(tempfile.gettempdir(), "nextup_phoneremote"))

results = []
def check(name, ok, detail=""):
    ok = bool(ok); results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- %s" % (detail,)) if detail != "" else ""))

def raises(fn, *a):
    try:
        fn(*a)
    except n.AppError as exc:
        return str(exc) or True
    return False

# --- a pretend mpv ---------------------------------------------------------------------
MPV = {"volume": 50, "mute": False, "pause": False, "audio-delay": 0.0,
       "time-pos": 600.0, "duration": 6000.0, "track-list": [], "idle-active": False}
SENT = []
ALIVE = [True]
def fake_get(name, default=None):
    return MPV.get(name, default)
def fake_cmd(*a):
    SENT.append(a)
    if a[0] == "set_property":
        MPV[a[1]] = {"yes": True, "no": False}.get(a[2], a[2])
    elif a[0] == "cycle" and a[1] in ("pause", "mute"):
        MPV[a[1]] = not MPV[a[1]]
    elif a[0] == "seek":
        MPV["time-pos"] = float(a[1]) if a[2] == "absolute" else MPV["time-pos"] + float(a[1])
n.mpv_get, n.mpv_command, n.mpv_alive = fake_get, fake_cmd, lambda: ALIVE[0]
n.note_audio_delay = lambda: None

def film_playing():
    conn = n.db()
    row = conn.execute("SELECT id, title FROM movies WHERE tmdb_id IS NOT NULL AND tmdb_id<>'' LIMIT 1").fetchone()
    conn.close()
    n.NOW_PLAYING.update(type="movie", id=row["id"], title=row["title"], sub="1999", art=None,
                         started_at=time.time() - 600, channel=None, channel_id=None,
                         position=600.0, duration=6000.0)
    return row
class Alive:
    def poll(self): return None
n._PLAY_PROC[0] = Alive()
film = film_playing()

# --- Task 1: one set of actions ----------------------------------------------------------
check("the actions are named", set(n.REMOTE_ACTIONS) == {"volume", "toggle", "channel", "delay", "episode",
                                                          "skip", "subtitles", "stop", "seek", "afk"})
a = n.remote_do("volume", {"delta": 5}); b = n.remote_do("volume", {"delta": 5})
check("volume +5 twice: each answers with the state after it", a["volume"] == 55 and b["volume"] == 60,
      (a["volume"], b["volume"]))
st = n.remote_do("toggle", {"what": "pause"})
check("pause toggles", st["paused"] is True, st["paused"])
n.remote_do("toggle", {"what": "pause"})
check("audio delay in ms", n.remote_do("delay", {"delta": -100})["audio_delay"] == -100)
n.remote_do("seek", {"to": 30})
check("seek to a point", ("seek", "30", "absolute") in SENT, SENT[-1:])
n.remote_do("seek", {"by": -9999})
check("seeking back past the start stops at 0", MPV["time-pos"] == 0, MPV["time-pos"])
n.remote_do("seek", {"to": 999999})
check("seeking past the end stops just short of it", MPV["time-pos"] == 5999, MPV["time-pos"])
st = n.remote_state()
check("the state says where it is and what it is",
      st.get("position") is not None and st.get("duration") == 6000 and st.get("title") == film["title"]
      and "afk" in st, {k: st.get(k) for k in ("position", "duration", "title", "afk")})
n._LAST_SEEN[0] = time.time() - 4 * 3600
n.afk_mid_file("movie", 600.0)
check("a pending question shows in the state", bool(n.remote_state().get("afk")))
n.remote_do("afk", {"still": True})
check("and is answered from the remote", n.afk_state() is None and MPV["pause"] is False)
check("an unknown control is refused", raises(n.remote_do, "selfdestruct", {}))
ALIVE[0] = False
check("nothing playing: said, not a crash", raises(n.remote_do, "volume", {"delta": 5}) == "Nothing is playing.")
ALIVE[0] = True

desk = n.ThreadingHTTPServer(("127.0.0.1", 8791), n.Handler)
threading.Thread(target=desk.serve_forever, daemon=True).start()
def desk_post(path, body):
    req = urllib.request.Request("http://127.0.0.1:8791" + path, data=json.dumps(body).encode(),
                                 method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())
before = MPV["volume"]
got = desk_post("/api/remote/volume", {"delta": 5})
check("the desktop remote goes through the same actions", got["volume"] == before + 5, got.get("volume"))

# The rest of the suite (tasks 2 and 3) appends below this line.
desk.shutdown()
print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
