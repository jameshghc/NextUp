# -*- coding: utf-8 -*-
"""The "are you still watching?" timer, checked against an isolated copy of
everything the app writes. Nothing here touches X:\\NextUp."""
import os, sys, time, tempfile, calendar

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import devserve
import nextup as n

SANDBOX = os.path.join(tempfile.gettempdir(), "nextup_afk_test")
devserve.isolate(n, SANDBOX)

PASS = []
FAIL = []


def check(name, got, want):
    (PASS if got == want else FAIL).append((name, got, want))


def stamp(hour, minute=0):
    """A local-time timestamp for today at that hour."""
    t = list(time.localtime())
    t[3], t[4], t[5] = hour, minute, 0
    return time.mktime(tuple(t))


# --- the settings -------------------------------------------------------------
n.CONFIG["afk"] = {}
check("defaults: late", n.afk_settings()["late"], 90)
check("defaults: enabled", n.afk_settings()["enabled"], True)

n.CONFIG["afk"] = {"late": "90", "day": -5, "evening": "nonsense",
                   "enabled": 0, "bogus": 1}
s = n.afk_settings()
check("a string of digits is a number", s["late"], 90)
check("a negative clamps to zero", s["day"], 0)
check("nonsense falls back to the default", s["evening"], 150)
check("enabled is a bool", s["enabled"], False)
check("unknown keys are dropped", "bogus" in s, False)

# --- the bands ----------------------------------------------------------------
check("half past midnight is late", n.afk_band(stamp(0, 30)), "late")
check("5:59am is still late", n.afk_band(stamp(5, 59)), "late")
check("six in the morning is day", n.afk_band(stamp(6)), "day")
check("five in the afternoon is day", n.afk_band(stamp(17)), "day")
check("six in the evening is evening", n.afk_band(stamp(18)), "evening")
check("eleven at night is evening", n.afk_band(stamp(23, 59)), "evening")

# --- should it ask? -----------------------------------------------------------
n.CONFIG["afk"] = {"enabled": True, "late": 45, "day": 240, "evening": 150}
band = n.afk_band()
limit = n.afk_settings()[band] * 60

n.seen_you()
check("just touched: no", n.afk_should_ask(), False)
n._LAST_SEEN[0] = time.time() - (limit - 60)
check("a minute short of the limit: no", n.afk_should_ask(), False)
n._LAST_SEEN[0] = time.time() - (limit + 60)
check("a minute past the limit: yes", n.afk_should_ask(), True)

n.CONFIG["afk"] = {"enabled": False}
check("switched off: never", n.afk_should_ask(), False)
n.CONFIG["afk"] = {"enabled": True, band: 0}
check("zero for this band: never", n.afk_should_ask(), False)
n.CONFIG["afk"] = {"enabled": True}

# --- mpv's own keyboard -------------------------------------------------------
PAUSED = [False]
n.mpv_get = lambda name, default=None: PAUSED[0] if name == "pause" else default


def replay(steps):
    """Feed the watcher a run of (seconds elapsed, position, paused) and say
    whether it decided somebody was there."""
    n._MPV_SEEN.update(at=0.0, pos=None, paused=None)
    n._LAST_SEEN[0] = 0.0
    base, real = time.time(), time.time
    try:
        for wall, pos, paused in steps:
            PAUSED[0] = paused
            time.time = lambda t=base + wall: t
            n.afk_watch_mpv(pos)
    finally:
        time.time = real
    return n._LAST_SEEN[0] > 0


check("playing along normally is nobody",
      replay([(0, 100, False), (1, 101, False), (2, 102, False)]), False)
check("jumping ahead is somebody",
      replay([(0, 100, False), (1, 160, False)]), True)
check("going back is somebody",
      replay([(0, 100, False), (1, 40, False)]), True)
check("pausing is somebody",
      replay([(0, 100, False), (1, 101, True)]), True)
check("unpausing is somebody",
      replay([(0, 100, True), (1, 100, False)]), True)
check("a stalled drive is not somebody",
      replay([(0, 100, False), (6, 101, False)]), False)
check("sitting paused is not somebody",
      replay([(0, 100, True), (1, 100, True), (2, 100, True)]), False)

# The trap: at a hand-over the position drops from the end of one file to
# the start of the next, which is a rewind to anything watching positions.
check("an episode change would look like a rewind",
      replay([(0, 1400, False), (1, 3, False)]), True)


def replay_over_handover():
    """The same two ticks, with the tracker told a new file has started."""
    n._MPV_SEEN.update(at=0.0, pos=None, paused=None)
    n._LAST_SEEN[0] = 0.0
    base, real = time.time(), time.time
    try:
        time.time = lambda: base
        n.afk_watch_mpv(1400)
        n.afk_new_file()
        time.time = lambda: base + 1
        n.afk_watch_mpv(3)
    finally:
        time.time = real
    return n._LAST_SEEN[0] > 0


check("a hand-over does not count as somebody", replay_over_handover(), False)

# --- what would follow --------------------------------------------------------
QUEUE = [0]
n.queue_count = lambda: QUEUE[0]
n.next_episode_after = lambda eid: {"episodeid": 99} if eid == 1 else None

check("a channel follows", n._would_follow({"type": "movie", "id": 5}, "comedy"), True)
QUEUE[0] = 2
check("a queue follows", n._would_follow({"type": "movie", "id": 5}, None), True)
QUEUE[0] = 0
check("a film alone follows nothing",
      n._would_follow({"type": "movie", "id": 5}, None), False)
check("an episode with another after it follows",
      n._would_follow({"type": "episode", "id": 1}, None), True)
check("the last episode follows nothing",
      n._would_follow({"type": "episode", "id": 2}, None), False)

# --- holding the hand-over ----------------------------------------------------
CALLS = []
n.mpv_command = lambda *a: CALLS.append(a)
n.mpv_alive = lambda: True
n.raise_app_window = lambda: CALLS.append(("raise",))
HANDED = []
n._hand_over = lambda current, follow_on: HANDED.append((current.get("id"), follow_on))
n._play_display = lambda kind, item_id: ("The Next Show", "S01E02 · Two", None)


def playing(kind="episode", item_id=1, title="My Hero Academia"):
    n._KEEP_OPEN[0] = False
    n.NOW_PLAYING.update(type=kind, id=item_id, title=title, sub="S01E01",
                         art=None, started_at=time.time() - 1500,
                         channel=None, channel_id=None,
                         position=1400, duration=1440)


# awake: it just hands over
CALLS[:] = []; HANDED[:] = []
n.seen_you()
playing()
n._finish_current("ended")
check("awake, it hands over", HANDED, [(1, None)])
check("awake, nothing is asked", n.afk_state(), None)

# asleep: it holds and asks
CALLS[:] = []; HANDED[:] = []
n._LAST_SEEN[0] = time.time() - 4 * 3600
playing()
n._finish_current("ended")
check("asleep, nothing hands over", HANDED, [])
state = n.afk_state()
check("asleep, the question is up", bool(state), True)
check("it names what finished", state["title"], "My Hero Academia")
check("it names what is next", state["next"], "The Next Show · S01E02 · Two")
check("it says how long", state["idle"] >= 239, True)
check("mpv comes out of fullscreen",
      ("set_property", "fullscreen", "no") in CALLS, True)
check("mpv is told", any(c[0] == "show-text" for c in CALLS), True)
check("the app is raised", ("raise",) in CALLS, True)

# ...and yes puts on exactly what was held
CALLS[:] = []; HANDED[:] = []
check("answered", n.afk_answer(True), True)
check("yes hands over what was held", HANDED, [(1, None)])
check("yes is being there", n.afk_should_ask(), False)
check("the question is gone", n.afk_state(), None)
check("answering twice does nothing", n.afk_answer(True), False)

# ...and no closes the player
n._LAST_SEEN[0] = time.time() - 4 * 3600
playing()
n._finish_current("ended")
CALLS[:] = []; HANDED[:] = []
n.afk_answer(False)
check("no closes the player", ("quit",) in CALLS, True)
check("no starts nothing", HANDED, [])

# --- no answer at all ---------------------------------------------------------
n._LAST_SEEN[0] = time.time() - 4 * 3600
playing()
n._finish_current("ended")
CALLS[:] = []
n.afk_tick()
check("inside the grace it waits", n.afk_state() is None, False)
check("inside the grace nothing closes", ("quit",) in CALLS, False)
n.ASK["since"] = time.time() - 6 * 60
n.afk_tick()
check("past the grace the player closes", ("quit",) in CALLS, True)
check("past the grace the question goes", n.afk_state(), None)

# the player closed by hand while the question was up
n._LAST_SEEN[0] = time.time() - 4 * 3600
playing()
n._finish_current("ended")
CALLS[:] = []
n.mpv_alive = lambda: False
n.afk_tick()
check("a player already gone just clears", n.afk_state(), None)
check("and nothing is sent to it", CALLS, [])
n.mpv_alive = lambda: True

# --- putting something else on is an answer -----------------------------------
n._LAST_SEEN[0] = time.time() - 4 * 3600
playing()
n._finish_current("ended")
check("the question is up", bool(n.afk_state()), True)
n.afk_clear()
check("starting something else clears it", n.afk_state(), None)

# --- a closed player is never a hand-over -------------------------------------
CALLS[:] = []; HANDED[:] = []
n._LAST_SEEN[0] = time.time() - 4 * 3600
playing()
n._finish_current("closed")
check("closing the window asks nothing", n.afk_state(), None)
check("closing the window hands over nothing", HANDED, [])

# --- the app's own buttons count as being there -------------------------------
# Not reachable without a request, so the check is that the hook is there at
# all, and before anything that can raise.
import inspect
body = inspect.getsource(n.Handler.do_POST).splitlines()
first = [ln.strip() for ln in body if ln.strip()
         and not ln.strip().startswith("#")][1:4]
check("every POST notices you", "seen_you()" in first, True)
check("it notices before the body is read",
      first.index("seen_you()") < first.index("data = self.read_body()"), True)

print()
for name, got, want in FAIL:
    print("FAIL  %-44s got %r, wanted %r" % (name, got, want))
print("%d/%d checks passed" % (len(PASS), len(PASS) + len(FAIL)))
