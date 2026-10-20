"""A friend's first run of 0.2: the rough edges the release prep found on a
fresh install, each pinned. Against a sandbox copy (devserve.isolate)."""
import sys, os, re, tempfile, shutil
sys.path.insert(0, r"X:\NextUp"); os.chdir(r"X:\NextUp"); sys.argv = ["nextup.py"]
import nextup as n
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from devserve import isolate
HOME = os.path.join(tempfile.gettempdir(), "nextup_firstrun")
isolate(n, HOME)

results = []
def check(name, ok, detail=""):
    ok = bool(ok); results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- %s" % (detail,)) if detail != "" else ""))

# --- mpv just installed by winget is found without restarting ----------------------
fake = os.path.join(HOME, "localappdata")
pkg = os.path.join(fake, "Microsoft", "WinGet", "Packages", "shinchiro.mpv_Microsoft.Winget.Source_8wekyb3d8bbwe")
os.makedirs(pkg, exist_ok=True)
open(os.path.join(pkg, "mpv.exe"), "wb").close()
saved = (os.environ.get("LOCALAPPDATA"), n.MPV_GUESSES, n.shutil.which, n.CONFIG.get("mpv_path"))
os.environ["LOCALAPPDATA"] = fake
n.MPV_GUESSES = []
n.shutil.which = lambda name: None
n.CONFIG["mpv_path"] = ""
try:
    got = n.find_mpv()
except n.AppError as exc:
    got = str(exc)
check("mpv installed by winget a moment ago is found", got == os.path.join(pkg, "mpv.exe"), got)
os.environ["LOCALAPPDATA"] = saved[0] or ""
n.MPV_GUESSES, n.shutil.which = saved[1], saved[2]
n.CONFIG["mpv_path"] = saved[3] or ""

# --- a fresh install has no resume folder yet: no alarm ---------------------------
conn = n.db()
conn.execute("UPDATE movies SET resume_pos=0"); conn.execute("UPDATE episodes SET resume_pos=0")
conn.commit(); conn.close()
shutil.rmtree(n.WATCH_LATER, ignore_errors=True)
if os.path.exists(n.ERROR_LOG):
    os.remove(n.ERROR_LOG)
n._RESUME_UNREADABLE_SAID[0] = False
n.sync_playback_state()
log = open(n.ERROR_LOG, encoding="utf-8").read() if os.path.exists(n.ERROR_LOG) else ""
check("a fresh install's missing resume folder is simply made, not logged as a problem",
      os.path.isdir(n.WATCH_LATER) and "resume folder" not in log, (os.path.isdir(n.WATCH_LATER), log[-200:]))

# --- the OneDrive offer waits until there's a library -------------------------------
check("an empty library isn't asked to share yet", "library_is_empty()" in
      open(os.path.join(r"X:\NextUp", "nextup.py"), encoding="utf-8").read().split('"offer":', 1)[1][:200])
check("this library isn't empty", n.library_is_empty() is False)
conn = n.db(); conn.execute("DELETE FROM movies"); conn.execute("DELETE FROM shows"); conn.commit(); conn.close()
check("an empty one is", n.library_is_empty() is True)

# --- the exe finds its fonts, logo and icon inside itself ---------------------------
src = open(os.path.join(r"X:\NextUp", "nextup.py"), encoding="utf-8").read()
check("frozen, the fonts, logo and icon come from inside the exe",
      'ASSET_DIR = getattr(sys, "_MEIPASS", HERE)' in src
      and 'FONTS_DIR = os.path.join(ASSET_DIR, "nextup_fonts")' in src
      and 'LOGO_PATH = os.path.join(ASSET_DIR, "nextup_logo.png")' in src)

# --- the page --------------------------------------------------------------------
page = n.PAGE
scan = page[page.find("$('#scanlib').onclick"):][:500]
check("SCAN saves the folders you typed before scanning", "media_folders" in scan)
check("no personal example paths", 'placeholder="E:\\\\Torrents"' not in page and "E:\\Torrents\"" not in page)
check("the firewall hint names Next Up, not Python", "whether Python can" not in page
      and "whether Next Up can" in page)
_msg = page[page.find("const plural = (k, one, many)"):][:1100]
check("the scan summary says plurals properly", "plural(" in _msg)
check("without a TMDB key it doesn't claim things failed to match", "STATUS.has_key" in _msg[:_msg.find("didn")]
      or "c.unidentified && STATUS.has_key" in _msg)

print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
