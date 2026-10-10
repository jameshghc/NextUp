"""nextup.py as the Android app runs it: data in a folder of its own, the
server started headless, and PLATFORM saying android.

Run in a SUBPROCESS with NEXTUP_HOME pointed at a scratch folder, because
the data paths are decided when the module is imported — the same moment
the app on the phone decides them."""
import sys, os, json, subprocess, tempfile, shutil

here = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(here)

results = []
def check(name, ok, detail=""):
    ok = bool(ok); results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- %s" % (detail,)) if detail != "" else ""))

home = os.path.join(tempfile.gettempdir(), "nextup_androidcore")
shutil.rmtree(home, ignore_errors=True)
os.makedirs(home)

PROBE = r'''
import sys, os, json, socket, threading, urllib.request, urllib.error
sys.argv = ["nextup.py"]
sys.path.insert(0, r"%s")
import nextup as n
out = {"platform": n.PLATFORM}
for name in ("CONFIG_PATH", "DB_PATH", "ERROR_LOG", "ART_DIR", "WATCH_LATER",
             "PLAY_STATE_PATH", "RECS_PATH", "CACHE_PATH", "YOUTUBE_PATH",
             "PHONE_SYNC_DIR", "DISMISS_PATH", "FONTS_DIR", "LOGO_PATH"):
    out[name] = getattr(n, name)
conn = n.db()
conn.execute("INSERT OR IGNORE INTO dismissed (key,at) VALUES ('movie:424242','x')")
conn.commit(); conn.close()
n.DISMISSED.clear()
n.ANDROID_VIDEO_ACCESS = lambda: False
held = socket.socket(); held.bind(("127.0.0.1", 8794)); held.listen(1)
port = n.serve_in_thread(8794)
out["port"] = port
with urllib.request.urlopen("http://127.0.0.1:%%d/" %% port, timeout=10) as r:
    body = r.read()
    out["status"], out["has_title"] = r.status, b"<title>" in body
    out["android_body"] = b'<body class="android">' in body
out["dismissed_loaded"] = "movie:424242" in n.DISMISSED
out["again"] = n.serve_in_thread(8797)
with urllib.request.urlopen("http://127.0.0.1:%%d/api/status" %% port, timeout=10) as r:
    out["status_payload"] = json.loads(r.read())
# Play: handed to the phone's mpv app, never a desktop mpv looked for.
handed = []
n.ANDROID_PLAYER = lambda path, start: handed.append([path, start])
film = os.path.join(os.getcwd(), "Phone Film (2001).mkv")
open(film, "wb").write(b"x" * 1000)
conn = n.db()
fid = conn.execute("INSERT INTO movies (path,title,year,resume_pos,resume_total) VALUES (?,?,?,?,?)",
                   (film, "Phone Film", 2001, 600, 6000)).lastrowid
conn.commit(); conn.close()
n.LOCAL.loaded_at = 0
def post(path, body):
    req = urllib.request.Request("http://127.0.0.1:%%d%%s" %% (port, path), method="POST",
                                 data=json.dumps(body).encode())
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())
out["play"] = post("/api/play", {"type": "movie", "id": fid})
out["play_resume"] = post("/api/play", {"type": "movie", "id": fid, "resume": True})
out["handed"] = handed
out["film"] = film
out["now_playing"] = n.NOW_PLAYING.get("type")
# mpv closing: where it stopped, then once seen to the end.
def row():
    c = n.db(); r = c.execute("SELECT resume_pos, playcount FROM movies WHERE id=?", (fid,)).fetchone(); c.close()
    return [r["resume_pos"], r["playcount"]]
n.android_play_finished(position=1500, duration=6000, completed=False)
out["after_stop"] = row()
post("/api/play", {"type": "movie", "id": fid})
out["handed_after_stop"] = handed[-1]
# mpv closing at the end straight after opening — a file it couldn't play
# closes the same way — isn't a film watched.
n._ANDROID_SITTING["started_at"] = n.time.time()
n.android_play_finished(position=None, duration=None, completed=True)
out["closed_at_once"] = row()
post("/api/play", {"type": "movie", "id": fid})
n._ANDROID_SITTING["started_at"] = n.time.time() - 3600
n.android_play_finished(position=None, duration=None, completed=True)
out["after_end"] = row()
n.android_play_finished(position=10, duration=6000, completed=False)
out["stray_finish"] = row()
with urllib.request.urlopen("http://127.0.0.1:%%d/api/mpv/test" %% port, timeout=30) as r:
    out["mpv_test"] = json.loads(r.read())
n.ANDROID_PLAYER = None
out["no_player"] = post("/api/play", {"type": "movie", "id": fid})
# The swap over the cable, the phone's half: the PC's events in, its own out.
conn = n.db()
sid = conn.execute("INSERT INTO movies (path,title,year,tmdb_id,playcount) VALUES (?,?,?,?,0)",
                   (film + ".shared.mkv", "Shared Film", 2002, "sh1")).lastrowid
conn.commit(); conn.close()
n.LOCAL.loaded_at = 0; n.LIB.loaded_at = 0
def pc_event(uid, event, **extra):
    ev = {"v": 1, "uid": uid, "utc": 1790000000 + int(uid[1:]) * 60, "device_id": "pc-desk",
          "device": "DESKTOP", "kind": "movie", "tmdb": "sh1", "season": None, "episode": None,
          "show": None, "title": "Shared Film", "event": event, "value": None, "seconds": None,
          "position": None, "total": None}
    ev.update(extra)
    return json.dumps(ev)
text = "\n".join([pc_event("e1", "favourited"), pc_event("e2", "watched"),
                   pc_event("e3", "stopped", position=1234, total=6000)]) + "\n"
out["share_in"] = post("/api/share/import", {"text": text})
c = n.db()
r = c.execute("SELECT favourited_at, resume_pos, playcount FROM movies WHERE id=?", (sid,)).fetchone()
out["shared_row"] = [bool(r["favourited_at"]), r["resume_pos"], r["playcount"]]
c.close()
with urllib.request.urlopen("http://127.0.0.1:%%d/api/share/export" %% port, timeout=30) as resp:
    exp = json.loads(resp.read())
out["share_out"] = {"device_id": exp.get("device_id"), "own": n.sync_device_id(),
                    "lines": [json.loads(x) for x in exp.get("text", "").splitlines() if x.strip()]}
out["threads"] = sorted(t.name for t in threading.enumerate())
print("JSON" + json.dumps(out))
''' % ROOT

before = sorted(os.listdir(ROOT))
env = dict(os.environ, NEXTUP_HOME=home, NEXTUP_PLATFORM="android", PYTHONDONTWRITEBYTECODE="1")
proc = subprocess.run([sys.executable, "-c", PROBE], capture_output=True, text=True,
                      encoding="utf-8", errors="replace", env=env, cwd=home, timeout=120)
line = next((l for l in proc.stdout.splitlines() if l.startswith("JSON")), None)
out = json.loads(line[4:]) if line else {}
if not out or "handed" not in out:
    print(proc.stdout[-1500:], proc.stderr[-1500:])

data_names = ("CONFIG_PATH", "DB_PATH", "ERROR_LOG", "ART_DIR", "WATCH_LATER", "PLAY_STATE_PATH",
              "RECS_PATH", "CACHE_PATH", "YOUTUBE_PATH", "PHONE_SYNC_DIR", "DISMISS_PATH")
stray = [k for k in data_names if not str(out.get(k, "")).lower().startswith(home.lower())]
check("every data path is under NEXTUP_HOME", out and not stray, stray)
check("assets stay with the code", out and all(str(out.get(k, "")).lower().startswith(ROOT.lower())
                                              for k in ("FONTS_DIR", "LOGO_PATH")),
      (out.get("FONTS_DIR"), out.get("LOGO_PATH")))
check("PLATFORM is android", out.get("platform") == "android", out.get("platform"))
check("serve picks another port when busy, and answers with the page",
      (out.get("port") or 0) > 8794 and out.get("status") == 200 and out.get("has_title"),
      (out.get("port"), out.get("status")))
check("no player monitor on android", out and "playback monitor" not in out.get("threads", []),
      out.get("threads"))
check("hidden suggestions are loaded at start-up", out.get("dismissed_loaded"))
check("starting twice reuses the first server", out.get("again") == out.get("port")
      and out.get("threads", []).count("server") == 1 and out.get("threads", []).count("sync") == 1,
      (out.get("again"), out.get("threads")))
check("no access to videos is said, not left as an empty library",
      "access to your videos" in json.dumps(out.get("status_payload") or {}),
      (out.get("status_payload") or {}).get("error"))
check("nothing written beside the code", sorted(os.listdir(ROOT)) == before,
      set(os.listdir(ROOT)) ^ set(before))

# main() can't be run here — it opens the window — so its names are checked
# instead: every one it reads must be assigned in it, defined in the module,
# or built in. When serve_in_thread took over the start-up, `server` stopped
# being assigned in main() but was still read there on the way out, and the
# app showed a NameError every time its window closed.
import symtable, builtins
src = open(os.path.join(ROOT, "nextup.py"), encoding="utf-8").read()
table = symtable.symtable(src, "nextup.py", "exec")
module_names = set(table.get_identifiers())
main_table = next(t for t in table.get_children() if t.get_name() == "main")
undefined = sorted(s.get_name() for s in main_table.get_symbols()
                   if s.is_referenced() and not s.is_assigned() and not s.is_parameter()
                   and not s.is_imported() and s.get_name() not in module_names
                   and not hasattr(builtins, s.get_name()))
check("main() uses no name it never defines", not undefined, undefined)

# --- a restart on the phone keeps every watch point ------------------------------------
# On the PC, mpv's own resume files are the truth, and a point with no file
# means "watched to the end". The phone's mpv is another app with no such
# files, so that rule wiped every watch point — and counted a watch — on the
# first library load after each start. And the repair: points put back from
# the phone's own history, play counts rebuilt.
WIPE = r"""
import sys, os, json
sys.argv = ["nextup.py"]
sys.path.insert(0, r"%s")
import nextup as n
conn = n.db()
def film(title, tmdb, pos, plays):
    return conn.execute("INSERT INTO movies (path,title,year,tmdb_id,resume_pos,resume_total,playcount)"
                        " VALUES (?,?,?,?,?,?,?)", ("/phone/%%s.mkv" %% title, title, 2000, tmdb,
                                                   pos, 7000, plays)).lastrowid
kept = film("Kept", "w1", 1518, 0)
# What the old rule did: wiped (0) and counted (3) — history knows better.
wiped = film("Wiped", "w2", 0, 3)
done = film("Done", "w3", 0, 2)
conn.execute("INSERT INTO snapshot_movies (tmdb_id,title,playcount) VALUES ('w3','Done',1)")
for kind, iid, title, ev, pos in (("movie", wiped, "Wiped", "played", None),
                                  ("movie", wiped, "Wiped", "stopped", 1200),
                                  # then a play the wipe sent back to the start
                                  ("movie", wiped, "Wiped", "played", None),
                                  ("movie", wiped, "Wiped", "stopped", 3),
                                  ("movie", done, "Done", "stopped", 300),
                                  ("movie", done, "Done", "watched", None)):
    conn.execute("INSERT INTO history (at,kind,item_id,title,event,position,total) VALUES (?,?,?,?,?,?,?)",
                 ("2026-10-09 00:00:00", kind, iid, title, ev, pos, 7000 if pos else None))
conn.commit(); conn.close()
n.LIB.load(force=True); n.LOCAL.load(force=True)
n.repair_android_resume()
c = n.db()
row = lambda i: list(c.execute("SELECT resume_pos, playcount FROM movies WHERE id=?", (i,)).fetchone())
out = {"kept": row(kept), "wiped": row(wiped), "done": row(done)}
n.repair_android_resume()            # once only
out["again"] = row(wiped)
print("JSON" + json.dumps(out))
""" % ROOT
home2 = os.path.join(tempfile.gettempdir(), "nextup_androidwipe")
shutil.rmtree(home2, ignore_errors=True); os.makedirs(home2)
proc2 = subprocess.run([sys.executable, "-c", WIPE], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=120, cwd=home2,
                       env=dict(os.environ, NEXTUP_HOME=home2, NEXTUP_PLATFORM="android",
                                PYTHONDONTWRITEBYTECODE="1"))
line2 = next((l for l in proc2.stdout.splitlines() if l.startswith("JSON")), None)
w = json.loads(line2[4:]) if line2 else {}
if not w:
    print(proc2.stdout[-800:], proc2.stderr[-1500:])
check("loading the library on the phone keeps a watch point, and counts no watch",
      w.get("kept") == [1518, 0], w.get("kept"))
check("the repair puts back the furthest point reached, not a restart's few seconds",
      (w.get("wiped") or [None])[0] == 1200, w.get("wiped"))
check("and rebuilds play counts: the PC's, plus what was really finished on the phone",
      (w.get("wiped") or [0, None])[1] == 0 and w.get("done") == [0, 2], (w.get("wiped"), w.get("done")))
check("the repair runs once", w.get("again") == w.get("wiped"), w.get("again"))
shutil.rmtree(home2, ignore_errors=True)

handed = out.get("handed") or []
check("PLAY on the phone picks up where you got to, as mpv does by itself on the PC",
      out.get("play", {}).get("ok") and handed[:1] == [[out.get("film"), 600]], (out.get("play"), handed))
check("RESUME hands it over with where you got to",
      len(handed) >= 2 and handed[1][1] == 600, handed)
check("stopping in mpv part way saves where you got to", out.get("after_stop") == [1500, None]
      or out.get("after_stop") == [1500, 0], out.get("after_stop"))
check("and the next PLAY starts there", (out.get("handed_after_stop") or [0, 0])[1] == 1500,
      out.get("handed_after_stop"))
check("closing at the end seconds after opening doesn't count as watched",
      out.get("closed_at_once") == [1500, 0], out.get("closed_at_once"))
check("seeing it to the end counts it watched, and clears the resume point",
      out.get("after_end") == [0, 1], out.get("after_end"))
check("a report from mpv with nothing playing changes nothing", out.get("stray_finish") == [0, 1],
      out.get("stray_finish"))
check("nothing claims to be playing: the player is another app, out of sight",
      out.get("now_playing") in (None, ""), out.get("now_playing"))
check("the mpv test in Settings says how the phone plays, not 'install mpv.exe'",
      out.get("mpv_test", {}).get("ok") and "mpv app" in out.get("mpv_test", {}).get("message", ""),
      out.get("mpv_test"))
share_out = out.get("share_out") or {}
lines = share_out.get("lines") or []
check("the phone takes in the PC's favourites and watch points",
      (out.get("shared_row") or [None])[0] and (out.get("shared_row") or [0, 0])[1] == 1234,
      out.get("shared_row"))
check("and no play is counted twice: the PC's counts come with the catalogue",
      (out.get("shared_row") or [0, 0, None])[2] == 0, out.get("shared_row"))
check("the phone hands over its own events, under its own id",
      share_out.get("device_id") == share_out.get("own") and lines
      and all(e.get("device_id") == share_out.get("own") for e in lines), share_out.get("device_id"))
check("and never the PC's back again", not any(e.get("uid") in ("e1", "e2", "e3") for e in lines))
check("no player hooked up is said plainly", "error" in (out.get("no_player") or {})
      and "winget" not in out["no_player"]["error"], out.get("no_player"))

check("the page is served marked as the phone's, for its phone-only rules",
      out.get("android_body"), out.get("android_body"))
page_src = open(os.path.join(ROOT, "nextup.py"), encoding="utf-8").read()
check("on the phone a details panel covers the top strip instead of scrolling under it",
      "body.android .sheet{" in page_src)
check("phone landscape: smaller tiles, and the search row and pager scroll with them",
      "@media (orientation:landscape) and (max-height:520px)" in page_src
      and "body.android #view-library{overflow-y:auto}" in page_src)
check("phone: a tap shows the peek — facts and colour-coded genres up top, PLAY, DETAILS below",
      "'play peekplay'" in page_src and "classList.add('peeking')" in page_src
      and "body.android .tile.peeking .peek{" in page_src and "peekdetails" in page_src
      and "function genreHue(" in page_src and "peektop" in page_src)
check("phone: a second tap on the poster closes the peek rather than opening details",
      "if(b.classList.contains('peeking')){ closePeeks(); return; }" in page_src)
check("phone Now: the pick in its own layout, Why this? on request",
      "function phonePick(" in page_src and 'id="whythis"' in page_src
      and "body.android #view-now:not(.hidden)" in page_src)
check("phone Favourites shows every favourite, not just the ones on the phone",
      "favWidened = true" in page_src)
check("phone Now: a step-by-step chooser — kind, then genres in their colours, then what fits",
      'id="nowchooser"' in page_src and "function chooserKind(" in page_src
      and "function chooserGenre(" in page_src and 'id="nowfits"' in page_src)
check("phone tile overlay: the heart and the bookmark in the corners their marks sit in",
      "body.android .tile .peek .peekmark.fav{" in page_src and "body.android .tile .peek .peekmark.watch{" in page_src)
check("a details panel can be swiped down to close", "function sheetSwipe(" in page_src
      and "sheetSwipe(back" in page_src)

# The phone's Back gesture asks the page first: close what's open, or say
# there's nothing, so the app can go to the background. Run in node against
# a pretend page: two details panels open, then none.
import re as _re
page_js = "\n;\n".join(_re.findall(r"<script>(.*?)</script>", open(os.path.join(ROOT, "nextup.py"),
                                     encoding="utf-8").read(), _re.S))
fn = _re.search(r"function nextupBack\(\)\{.*?\n\}", page_js, _re.S)
check("the page has a Back handler for the phone", fn, "")
if fn:
    probe = """
let tileMenu = null, queueOverlayOpen = false, peeking = 1;
const sheets = [{removed:false}, {removed:false}];
const document = {querySelectorAll: s => s === '.sheet'
  ? sheets.filter(x => !x.removed).map(x => ({remove(){ x.removed = true; }}))
  : s === '.tile.peeking' ? Array(peeking).fill({}) : []};
function closeTileMenu(){} function placeQueueSide(){} function closePeeks(){ peeking = 0; }
""" + fn.group(0) + """
console.log(JSON.stringify([nextupBack(), sheets[1].removed, sheets[0].removed, nextupBack(), sheets[0].removed, nextupBack(), peeking, nextupBack()]));
"""
    r = subprocess.run(["node", "-e", probe], capture_output=True, text=True)
    got = json.loads(r.stdout or "null")
    check("Back closes the top panel first, then the next, then an open tile peek, then says nothing's open",
          got == [True, True, False, True, True, True, 0, False], (got, r.stderr[:300]))

shutil.rmtree(home, ignore_errors=True)
print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
