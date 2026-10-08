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
import sys, os, json, socket, threading, urllib.request
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
    out["status"], out["has_title"] = r.status, b"<title>" in r.read()
out["dismissed_loaded"] = "movie:424242" in n.DISMISSED
out["again"] = n.serve_in_thread(8797)
with urllib.request.urlopen("http://127.0.0.1:%%d/api/status" %% port, timeout=10) as r:
    out["status_payload"] = json.loads(r.read())
out["threads"] = sorted(t.name for t in threading.enumerate())
print("JSON" + json.dumps(out))
''' % ROOT

before = sorted(os.listdir(ROOT))
env = dict(os.environ, NEXTUP_HOME=home, NEXTUP_PLATFORM="android", PYTHONDONTWRITEBYTECODE="1")
proc = subprocess.run([sys.executable, "-c", PROBE], capture_output=True, text=True,
                      encoding="utf-8", errors="replace", env=env, cwd=home, timeout=120)
line = next((l for l in proc.stdout.splitlines() if l.startswith("JSON")), None)
out = json.loads(line[4:]) if line else {}
if not out:
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

shutil.rmtree(home, ignore_errors=True)
print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
