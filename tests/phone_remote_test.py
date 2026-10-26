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
                                                          "skip", "subtitles", "stop", "seek", "afk",
                                                          "fullscreen", "power"})
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

# --- Task 2: the remote over the Wi-Fi ----------------------------------------------------
PHONE = "fedcba9876543210"
PORT = 8792
n.phone_link_start(PORT, "127.0.0.1")
token = n.phone_pair_direct(PHONE, "S21 Ultra")
def call(method, path, body=None, tok=token):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request("http://127.0.0.1:%d%s" % (PORT, path), data=data, method=method)
    if tok:
        req.add_header("Authorization", "Bearer " + tok)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except ValueError:
            return e.code, {}

PLAYED = []
n.require_media_file = lambda path: path
n.mpv_play = lambda path, start=0, keep_open=False: PLAYED.append((path, int(start or 0))) or Alive()
REAL_NOTE = n.note_now_playing
n.note_now_playing = lambda proc, kind, item_id, title, **k: n.NOW_PLAYING.update(
    type=kind, id=item_id, title=title, position=None, duration=None, channel=None, channel_id=None)

check("no token, no remote", call("GET", "/phone/remote/state", tok=None)[0] == 401)
st, state = call("GET", "/phone/remote/state")
check("the state over the wire", st == 200 and "volume" in state and "position" in state, (st, list(state)[:6]))
before = MPV["volume"]
st, got = call("POST", "/phone/remote/volume", {"delta": 5})
check("a control over the wire is the same action", st == 200 and got["volume"] == before + 5, (st, got.get("volume")))
check("an unknown control is 404", call("POST", "/phone/remote/selfdestruct", {})[0] == 404)
ALIVE[0] = False
st, got = call("POST", "/phone/remote/volume", {"delta": 5})
check("nothing playing: said, with the app's usual 200", st == 200 and got.get("error") == "Nothing is playing.", (st, got))
ALIVE[0] = True
n._LAST_SEEN[0] = time.time() - 4 * 3600
call("POST", "/phone/remote/toggle", {"what": "pause"})
check("a press on the phone counts as being there", n.afk_idle() < 5, round(n.afk_idle()))

conn = n.db()
mv = conn.execute("SELECT id, tmdb_id, path, title FROM movies WHERE tmdb_id<>'' AND path IS NOT NULL LIMIT 1").fetchone()
show_id = conn.execute("INSERT INTO shows (name,title,tmdb_id) VALUES ('remote test show','Remote Test Show','990011')").lastrowid
e1 = conn.execute("INSERT INTO episodes (path,show_id,season,episode,title) VALUES ('X:/rt/s1e1.mkv',?,1,1,'One')", (show_id,)).lastrowid
e2 = conn.execute("INSERT INTO episodes (path,show_id,season,episode,title) VALUES ('X:/rt/s1e2.mkv',?,1,2,'Two')", (show_id,)).lastrowid
conn.commit(); conn.close()
n.LIB.loaded_at = 0; n.LOCAL.loaded_at = 0
PLAYED.clear()
st, got = call("POST", "/phone/remote/play", {"kind": "movie", "tmdb": mv["tmdb_id"]})
check("Play on PC: a film", st == 200 and PLAYED and PLAYED[-1][0] == mv["path"], (st, got.get("error"), PLAYED[-1:]))
st, got = call("POST", "/phone/remote/play", {"kind": "episode", "tmdb": "990011", "season": 1, "episode": 2})
check("Play on PC: an episode", PLAYED[-1][0] == "X:/rt/s1e2.mkv", (got.get("error"), PLAYED[-1:]))
conn = n.db(); conn.execute("UPDATE episodes SET playcount=1, last_played='2026-10-01 20:00:00' WHERE id=?", (e1,)); conn.commit(); conn.close()
n.LIB.loaded_at = 0; n.LOCAL.loaded_at = 0
call("POST", "/phone/remote/play", {"kind": "tvshow", "tmdb": "990011"})
check("Play on PC: a show plays its next-up episode", PLAYED[-1][0] == "X:/rt/s1e2.mkv", PLAYED[-1:])
conn = n.db(); conn.execute("UPDATE episodes SET playcount=1, last_played='2026-10-02 20:00:00' WHERE id=?", (e2,)); conn.commit(); conn.close()
n.LIB.loaded_at = 0; n.LOCAL.loaded_at = 0
st, got = call("POST", "/phone/remote/play", {"kind": "tvshow", "tmdb": "990011"})
check("a show seen to the end starts again at the first episode", PLAYED[-1][0] == "X:/rt/s1e1.mkv",
      (got.get("error"), PLAYED[-1:]))
st, got = call("POST", "/phone/remote/play", {"kind": "pcid", "type": "movie", "id": mv["id"]})
check("Play on PC by the PC's own id (a title with no TMDB id)", st == 200 and PLAYED[-1][0] == mv["path"],
      (got.get("error"), PLAYED[-1:]))
st, got = call("POST", "/phone/remote/play", {"kind": "movie", "tmdb": "1"})
check("something this PC hasn't got is said", got.get("error") == "The PC doesn't have that any more.", got)

# Final review fixes.
n.NOW_PLAYING.update(position=600.0, duration=6000.0)   # as the monitor last saw it
st, got = call("POST", "/phone/remote/seek", {"to": 3600})
check("a seek answers with where it went, not where it was", got.get("position") == 3600, got.get("position"))
bad = [call("POST", "/phone/remote/play", {"kind": "episode", "tmdb": "990011", "season": "x", "episode": 1}),
       call("POST", "/phone/remote/seek", {"to": float("nan")}),
       call("POST", "/phone/remote/volume", {"value": "loud"})]
check("nonsense numbers are refused politely, never a 500 with Python's words",
      all(st == 200 and got.get("error") and "invalid literal" not in got["error"]
          and "could not convert" not in got["error"] for st, got in bad), bad)

n.NOW_PLAYING["art"] = "/art/abc123.jpg"
st, state = call("GET", "/phone/remote/state")
check("the art is something the phone can fetch", state.get("art") == "/phone/art/abc123.jpg", state.get("art"))
codes = {r: call("POST", "/phone/remote/" + r, {})[0] for r in ("../api/config", "presets", "state")}
check("only the listed remote routes answer", all(c == 404 for c in codes.values()), codes)
# --- Task 3: the phone's side ------------------------------------------------------------
# This process plays the phone now, reaching the PC half above on loopback.
n.PLATFORM = "android"
n.CONFIG["pc_link"] = {"token": token, "pc": "Test PC", "pc_id": "", "port": PORT,
                       "addresses": ["127.0.0.1"], "last_ip": None}
n.pc_link_check(force=True)
def desk_get(path):
    with urllib.request.urlopen("http://127.0.0.1:8791" + path, timeout=10) as r:
        return r.status, r.headers.get("Content-Type"), r.read()
st, kind, body = desk_get("/api/pcremote/state")
state = json.loads(body)
check("the phone passes the state through", st == 200 and "volume" in state, list(state)[:5])
check("with the picture as one the phone's own page can fetch",
      state.get("art") == "/api/pcremote/art/abc123.jpg", state.get("art"))
before = MPV["volume"]
got = desk_post("/api/pcremote/volume", {"delta": 5})
check("and a press", got.get("volume") == before + 5, got.get("volume"))
art_dir = n.ART_DIR
os.makedirs(art_dir, exist_ok=True)
open(os.path.join(art_dir, "abc123.jpg"), "wb").write(b"\xff\xd8fakejpeg")
st, kind, body = desk_get("/api/pcremote/art/abc123.jpg")
check("the picture itself comes through", st == 200 and body == b"\xff\xd8fakejpeg" and kind == "image/jpeg", (st, kind))

import socket as _socket
_real_urlopen = urllib.request.urlopen
def _slow(*a, **k):
    raise _socket.timeout("timed out")
n.urllib.request.urlopen = _slow
r = n.pc_link_call("POST", "/phone/remote/subtitles", {})
n.urllib.request.urlopen = _real_urlopen
check("a slow answer isn't the PC going away", n.PC_LINK["up"] is True and r[0] == 0, (n.PC_LINK["up"], r))

n.phone_link_stop()
n.PC_LINK.update(checked=0)
got = desk_post("/api/pcremote/volume", {"delta": 5})
check("PC gone: said plainly, nothing thrown", got.get("error") == "The PC isn't on the Wi-Fi right now.", got)
st, kind, body = desk_get("/api/pcremote/state")
check("the state says so too", json.loads(body).get("error") == "The PC isn't on the Wi-Fi right now.")

conn = n.db()
row = conn.execute("SELECT tmdb_id, title FROM movies WHERE tmdb_id<>'' LIMIT 1").fetchone()
conn.execute("INSERT OR REPLACE INTO snapshot_movies (tmdb_id,title,year) VALUES (?,?,2000)", (row["tmdb_id"], row["title"]))
conn.commit(); conn.close()
def mine():
    n.LIB.loaded_at = 0; n.LOCAL.loaded_at = 0
    out = n.browse_library("movie", row["title"], "title", "all", 50, 0)
    items = out.get("items") if isinstance(out, dict) else out
    return next((i for i in items if i.get("title") == row["title"] and not i.get("elsewhere")), {})
check("a film the PC has is not marked while the PC is away", not mine().get("on_pc"))
n.phone_link_start(PORT, "127.0.0.1")
n.pc_link_check(force=True)
check("and is marked on_pc while it's there", mine().get("on_pc") is True, {k: mine().get(k) for k in ("title", "on_pc")})
n.PLATFORM = "windows"

_copy = re.search(r'const PC_AWAY_COPY = "([^"]*)";', n.PAGE)
check("the page recognises the phone server's 'PC gone' words exactly",
      _copy and _copy.group(1).replace("\u2019", "’") == n.PC_AWAY, (_copy and _copy.group(1), n.PC_AWAY))

# --- Fullscreen and Power (2026-10-24) ---------------------------------------------------
ALIVE[0] = True
MPV["fullscreen"] = False
SENT.clear()
st = n.remote_do("fullscreen", {})
check("FULLSCREEN puts the player fullscreen", MPV["fullscreen"] is True and st.get("fullscreen") is True,
      (MPV["fullscreen"], st.get("fullscreen")))
time.sleep(0.8)
check("and pulls it to the front (on top for a moment, then not)",
      ("set_property", "ontop", True) in SENT and MPV.get("ontop") is False, [x for x in SENT if "ontop" in x])
n.remote_do("fullscreen", {})
check("pressed again, back to a window", MPV["fullscreen"] is False)
ALIVE[0] = False
check("FULLSCREEN with nothing playing says so", raises(n.remote_do, "fullscreen", {}) == "Nothing is playing.")

# Power: whatever was last on, fullscreen.
n.CONFIG.pop("last_sitting", None)
check("POWER with nothing ever played says so", raises(n.remote_do, "power", {}))
REAL_NOTE(Alive(), "movie", mv["id"], mv["title"])
check("starting something remembers it for POWER", n.CONFIG.get("last_sitting", {}).get("id") == mv["id"],
      n.CONFIG.get("last_sitting"))
st = n.remote_state()
check("the idle Remote can name it", st.get("last_title") == mv["title"], st.get("last_title"))
PLAYED.clear(); MPV["fullscreen"] = False
n.remote_do("power", {})
ALIVE[0] = True
time.sleep(1.0)
check("POWER starts the last film again", PLAYED and PLAYED[-1][0] == mv["path"], PLAYED[-1:])
check("fullscreen", MPV["fullscreen"] is True)
ALIVE[0] = False
conn = n.db()
conn.execute("UPDATE episodes SET playcount=1, resume_pos=0 WHERE id=?", (e1,))
conn.execute("UPDATE episodes SET playcount=0, resume_pos=0 WHERE id=?", (e2,))
conn.commit(); conn.close()
n.LIB.loaded_at = 0; n.LOCAL.loaded_at = 0
n.CONFIG["last_sitting"] = {"kind": "episode", "id": e1, "channel_id": None}
n.remote_do("power", {})
check("an episode seen to the end: POWER plays the next", PLAYED[-1][0] == "X:/rt/s1e2.mkv", PLAYED[-1:])
tuned = []
_real_tune = n.tune_channel
n.tune_channel = lambda channel, **k: tuned.append(channel["id"])
n.CONFIG["last_sitting"] = {"kind": "movie", "id": mv["id"], "channel_id": "comedy"}
n.remote_do("power", {})
n.tune_channel = _real_tune
check("a channel: POWER rejoins it", tuned == ["comedy"], tuned)
# The idle card: what POWER would do, in words.
conn = n.db(); conn.execute("UPDATE movies SET resume_pos=660, resume_total=1380 WHERE id=?", (mv["id"],)); conn.commit(); conn.close()
n.LOCAL.loaded_at = 0
n.CONFIG["last_sitting"] = {"kind": "movie", "id": mv["id"], "channel_id": None}
card = n.last_sitting_card()
check("the card: a film part way, how far and how long left",
      card and card["title"] == mv["title"] and card["percent"] == 47 and card["note"] == "Stopped 11 min in · 12 min left",
      card)
n.CONFIG["last_sitting"] = {"kind": "episode", "id": e1, "channel_id": None}
card = n.last_sitting_card()
check("an episode seen to the end: the card names the next one",
      card and card["note"] == "Next episode" and "S01E02" in (card["sub"] or ""), card)
ALIVE[0] = False
_st = n.phone_remote_state()
check("and the idle state carries it to the phone", (_st.get("last") or {}).get("note") == "Next episode", _st.get("last"))
check("the page has both buttons", 'data-a="fullscreen"' in n.PAGE and 'id="rm_power"' in n.PAGE)

# --- The PC's now-playing bar: a few controls (2026-10-25) --------------------------------
ALIVE[0] = True
MPV["pause"] = True; MPV["mute"] = False
film_playing()
with urllib.request.urlopen("http://127.0.0.1:8791/api/playing", timeout=10) as r:
    _pl = json.loads(r.read())
check("the bar's poll says whether it's paused and muted",
      _pl.get("paused") is True and _pl.get("muted") is False, {k: _pl.get(k) for k in ("paused", "muted")})
_req = urllib.request.Request("http://127.0.0.1:8791/api/remote/toggle", data=json.dumps({"what": "mute"}).encode(),
                              method="POST", headers={"Content-Type": "application/json"})
with urllib.request.urlopen(_req, timeout=10) as r:
    _st = json.loads(r.read())
check("the bar's buttons use the Remote's own actions", _st.get("muted") is True, _st.get("muted"))
_pb = n.PAGE[n.PAGE.find("function renderPlaying("):][:6000]
check("the bar has previous, play/pause, next, mute and close",
      all(x in _pb for x in ("'prevep'", "'pause'", "'nextep'", "'mute'", "'stop'")) and "pbctl" in _pb, "")

# The bar's title opens what's playing: a film's page, or an episode's show.
n.NOW_PLAYING.update(type="episode", id=e2, title="Remote Test Show", sub="S01E02", art=None,
                     started_at=time.time() - 60, channel=None, channel_id=None, position=60.0, duration=1500.0)
n.LIB.loaded_at = 0
with urllib.request.urlopen("http://127.0.0.1:8791/api/playing", timeout=10) as r:
    _pl = json.loads(r.read())
check("an episode playing: the poll says which show it's from", _pl.get("show_id") == show_id, _pl.get("show_id"))
film_playing()
_pb = n.PAGE[n.PAGE.find("function renderPlaying("):][:7000]
check("the bar's title opens the film, or the episode's show",
      "'pbtitle'" in _pb and "openFilm(p.id)" in _pb and "openShow(st.show_id)" in _pb, "")

# 2026-10-26: what's on opens its page from the phone's Remote.
_k = n.db()
_ep = _k.execute("SELECT e.id, e.season, s.tmdb_id FROM episodes e JOIN shows s ON s.id = e.show_id"
                 " WHERE s.tmdb_id IS NOT NULL AND s.tmdb_id != '' LIMIT 1").fetchone()
_mv = _k.execute("SELECT id, tmdb_id FROM movies WHERE tmdb_id IS NOT NULL AND tmdb_id != '' LIMIT 1").fetchone()
_k.close()
_oe = n.playing_ident({"type": "episode", "id": _ep["id"]})
check("an episode opens its show, at its season", _oe == {"kind": "tvshow", "tmdb": _ep["tmdb_id"], "season": _ep["season"]}, _oe)
check("a film opens itself", n.playing_ident({"type": "movie", "id": _mv["id"]}) == {"kind": "movie", "tmdb": _mv["tmdb_id"], "season": None})
check("a stream opens nothing", n.playing_ident({"type": "youtube", "id": "x"}) is None and n.playing_ident(None) is None)
_pg = n.PAGE
check("the phone's Remote makes it tappable", 'id="rm_now"' in _pg and "openShow(null, opens.tmdb, opens.season)" in _pg
      and "async function openShow(id, pcTmdb, atSeason)" in _pg)

desk.shutdown()
print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
