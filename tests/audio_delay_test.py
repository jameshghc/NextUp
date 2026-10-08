"""Audio delay remembered per film and per episode: set once, from the
remote or from mpv's own keys, and put back every time that file plays.

mpv is faked: commands are recorded, its properties are a dict, and a new
player is a recorded argument list rather than a process."""
import sys, os, tempfile, json, threading, urllib.request
sys.path.insert(0, r"X:\NextUp"); os.chdir(r"X:\NextUp"); sys.argv = ["nextup.py"]
import nextup as n
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from devserve import isolate
isolate(n, os.path.join(tempfile.gettempdir(), "nextup_audiodelay"))

results = []
def check(name, ok, detail=""):
    ok = bool(ok); results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- %s" % (detail,)) if detail != "" else ""))

# --- a pretend mpv ---------------------------------------------------------------
props = {"audio-delay": 0.0, "path": None}
cmds, launched = [], []
alive = [False]
def fake_command(*a):
    cmds.append(a)
    if a[:1] == ("set_property",):
        props[a[1]] = a[2]
    if a[:1] == ("loadfile",):
        props["path"] = a[1]
        opts = a[4] if len(a) > 4 else {}
        if "audio-delay" in opts:
            props["audio-delay"] = float(opts["audio-delay"])
    return {"error": "success"}
n.mpv_command = fake_command
n.mpv_get = lambda name, default=None: props.get(name, default)
n.mpv_alive = lambda: alive[0]
n.find_mpv = lambda: r"C:\fake\mpv.exe"
class FakeProc:
    pid = 1
    def poll(self): return None
import subprocess
subprocess.Popen = lambda args, **k: (launched.append(args), FakeProc())[1]

conn = n.db()
film = conn.execute("SELECT id, path FROM movies WHERE path IS NOT NULL ORDER BY id LIMIT 1").fetchone()
other = conn.execute("SELECT id, path FROM movies WHERE path IS NOT NULL ORDER BY id LIMIT 1 OFFSET 1").fetchone()
ep = conn.execute("SELECT id, path FROM episodes WHERE path IS NOT NULL ORDER BY id LIMIT 1").fetchone()
conn.execute("UPDATE movies SET audio_delay=NULL"); conn.execute("UPDATE episodes SET audio_delay=NULL")
conn.commit(); conn.close()
n.LOCAL.loaded_at = 0

def saved(table, rid):
    c = n.db(); v = c.execute("SELECT audio_delay FROM %s WHERE id=?" % table, (rid,)).fetchone()[0]; c.close()
    return v

def playing(kind, item_id, path):
    props["path"] = path
    n.NOW_PLAYING.update(type=kind, id=item_id, started_at=0)

# --- remembering ---------------------------------------------------------------------
playing("movie", film["id"], film["path"])
props["audio-delay"] = -0.1
n.note_audio_delay()
check("a delay set while a film plays is saved for that film", saved("movies", film["id"]) == -100,
      saved("movies", film["id"]))
props["audio-delay"] = -0.2
n.note_audio_delay()
check("changed again, the newest is kept", saved("movies", film["id"]) == -200, saved("movies", film["id"]))

# The moment of switching: the app still thinks the film is on, mpv already has the next file.
props["path"] = other["path"]; props["audio-delay"] = 0.0
n.note_audio_delay()
check("mid-switch, the next file's delay isn't written onto the last one",
      saved("movies", film["id"]) == -200, saved("movies", film["id"]))

playing("episode", ep["id"], ep["path"])
props["audio-delay"] = 0.3
n.note_audio_delay()
check("episodes each keep their own", saved("episodes", ep["id"]) == 300, saved("episodes", ep["id"]))

# --- putting it back --------------------------------------------------------------------
n.NOW_PLAYING.update(type=None, id=None)
alive[0] = False
n.mpv_play(film["path"])
args = launched[-1]
check("a new player opens the film with its saved delay", "--audio-delay=-0.200" in args, args)
n.mpv_play(other["path"])
check("and anything without one at 0", "--audio-delay=0.000" in launched[-1], launched[-1])

alive[0] = True
n.mpv_play(film["path"], keep_open=True)
load = [c for c in cmds if c[:1] == ("loadfile",)][-1]
check("loaded into an open window, it comes with the film's delay", load[4].get("audio-delay") == "-0.200", load)
n.mpv_play(other["path"], keep_open=True)
load = [c for c in cmds if c[:1] == ("loadfile",)][-1]
check("and the next file doesn't inherit it", load[4].get("audio-delay") == "0.000", load)

# --- the monitor and the remote save it --------------------------------------------------
import inspect
check("the playback monitor notices a delay set from mpv's own keys",
      "note_audio_delay()" in inspect.getsource(n._monitor_tick))
from http.server import ThreadingHTTPServer
desk = ThreadingHTTPServer(("127.0.0.1", 8787), n.Handler)
threading.Thread(target=desk.serve_forever, daemon=True).start()
playing("movie", other["id"], other["path"]); props["audio-delay"] = 0.0
req = urllib.request.Request("http://127.0.0.1:8787/api/remote/delay", method="POST",
                             data=json.dumps({"delta": -100}).encode())
urllib.request.urlopen(req, timeout=10).read()
check("the remote's -100ms is saved straight away", saved("movies", other["id"]) == -100, saved("movies", other["id"]))
desk.shutdown()

print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
