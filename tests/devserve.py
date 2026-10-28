"""Dev server for UI work: serves Next Up on 8771 (alongside the real app on
8770) against COPIES of everything it can write, so testing can click
anything without touching the user's real data.

History: this used to copy only the database. Settings were still saved to
the real nextup_config.json — and since this server blanks sync_folder so a
test can't write to OneDrive, clicking through the profile picker saved
that blank over the user's real settings and switched their sharing off.
Every path the app writes to is now redirected, and isolate() refuses to
start if any of them still points into X:\\NextUp. The routes that reach
real places outside the app — the Recycle Bin, the OneDrive sharing folder,
USB drives, the downloads folder — are switched off too.

Still shared with the real app, on purpose: the TMDB cache and the artwork
folder (both only ever added to, and a sandbox without them would refetch
everything), and mpv — PLAY and TEST MPV really do open a player."""
import sys, os, shutil, tempfile, json
sys.path.insert(0, r"X:\NextUp")
os.chdir(r"X:\NextUp")
sys.argv = ["nextup.py"]

import nextup
from http.server import ThreadingHTTPServer

SANDBOX = os.path.join(tempfile.gettempdir(), "nextup_devserve")


def isolate(n, sandbox):
    """Point every file the app writes at a scratch copy. Shared with the
    test scripts, which import this rather than repeating it."""
    os.makedirs(sandbox, exist_ok=True)
    live = r"X:\NextUp"
    db = os.path.join(sandbox, "nextup_library.db")
    shutil.copyfile(n.DB_PATH, db)
    n.DB_PATH = db
    n._MIGRATED[0] = False
    n.LIB.loaded_at = 0
    n.CONFIG_PATH = os.path.join(sandbox, "nextup_config.json")
    n.CONFIG["sync_folder"] = ""
    # The channels in the order the code lists them, not the one you've
    # set in the real app: the tests count on knowing which is which.
    # NEXTUP_KEEP_CHANNEL_ORDER=1 keeps yours, for screenshots that should
    # look like your own guide; the phone sandbox's pretend PC inherits it.
    if not os.environ.get("NEXTUP_KEEP_CHANNEL_ORDER"):
        n.CONFIG.pop("channel_order", None)
    if hasattr(n, "apply_channel_order"):
        n.apply_channel_order()
    with open(n.CONFIG_PATH, "w", encoding="utf-8") as fh:
        json.dump(n.CONFIG, fh)
    # The last suggestions, copied in so the Recommendations page has
    # something to show without a scan. Written back only in the sandbox.
    recs = os.path.join(sandbox, "nextup_recs.json")
    if os.path.isfile(n.RECS_PATH):
        shutil.copyfile(n.RECS_PATH, recs)
    n.RECS_PATH = recs
    n.PLAY_STATE_PATH = os.path.join(sandbox, "nextup_playing.json")
    # mpv's resume files, copied: with none, the app reads every watch point
    # as "played to the end" (see sync_playback_state), wiping them all and
    # stamping every half-watched thing as played just now.
    resume = os.path.join(sandbox, "nextup_resume")
    shutil.rmtree(resume, ignore_errors=True)
    if os.path.isdir(n.WATCH_LATER):
        shutil.copytree(n.WATCH_LATER, resume)
    n.WATCH_LATER = resume
    n.ERROR_LOG = os.path.join(sandbox, "nextup_errors.log")
    # The YouTube channels' video lists. Copied in when there is one, so
    # the sandbox's channel page matches the real one without a fetch.
    youtube = os.path.join(sandbox, "nextup_youtube.json")
    if os.path.isfile(n.YOUTUBE_PATH):
        shutil.copyfile(n.YOUTUBE_PATH, youtube)
    n.YOUTUBE_PATH = youtube
    # A paired phone's history, when cloud sharing is off. Starts empty: a
    # test that wants a phone pairs one.
    n.PHONE_SYNC_DIR = os.path.join(sandbox, "nextup_phone_sync")
    shutil.rmtree(n.PHONE_SYNC_DIR, ignore_errors=True)
    for name in ("DB_PATH", "CONFIG_PATH", "RECS_PATH", "PLAY_STATE_PATH",
                 "WATCH_LATER", "ERROR_LOG", "YOUTUBE_PATH", "PHONE_SYNC_DIR"):
        path = os.path.abspath(getattr(n, name))
        if path.lower().startswith(live.lower()):
            raise SystemExit("refusing to start: %s still points at %s" % (name, path))

    # The app's own files are sandboxed above. These are the routes that
    # reach REAL places OUTSIDE the app's folder, found by the first
    # ui-designer run, which kept clear of them on its own. Closed here so
    # nobody has to remember to: a test that needs one of them puts its own
    # stand-in back after calling isolate(), as dupes_test does with the bin.
    def refuse(what):
        def closed(*_a, **_k):
            raise n.AppError("Not in the sandbox: %s is switched off here." % what)
        return closed
    # The sandbox's library is a copy, but its paths point at the real media:
    # MOVE TO BIN in the duplicates review would bin real films.
    n.send_to_trash = refuse("the Recycle Bin")
    # SHARE THROUGH ONEDRIVE would write test history into the real sharing
    # folder, where the user's other computers would read it as theirs.
    n.cloud_folders = lambda: []
    n.sync_enable = refuse("sharing between devices")
    # The docking station copies to real USB drives.
    n.list_dock_drives = lambda: []
    n.dock_copy_worker = refuse("copying to a drive")
    # The copied config names the real downloads folder, where SORT THEM
    # moves real files. Tests that exercise the sorter set their own.
    n.CONFIG["downloads_folder"] = ""
    # The phone link opens a port on the home network. Off in the sandbox,
    # with no paired phones copied in; a test that wants it turns it on.
    n.CONFIG["phone_link"] = {"enabled": False, "devices": []}
    # And if one does, on this machine only, beside the real app's 8790:
    # every interface would mean a Windows Firewall prompt on the desktop.
    n.PHONE_HOST = "127.0.0.1"
    n.PHONE_PORT = 8791
    with open(n.CONFIG_PATH, "w", encoding="utf-8") as fh:
        json.dump(n.CONFIG, fh)


if __name__ == "__main__":
    isolate(nextup, SANDBOX)
    PORT = 8771
    nextup.load_saved_recs()
    print("devserve on http://127.0.0.1:%d (sandbox %s)" % (PORT, SANDBOX), flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), nextup.Handler).serve_forever()
