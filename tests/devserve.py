"""Dev server for UI work: serves Next Up on 8771 (alongside the real app on
8770) against COPIES of everything it can write, so testing can click
anything without touching the user's real data.

History: this used to copy only the database. Settings were still saved to
the real nextup_config.json — and since this server blanks sync_folder so a
test can't write to OneDrive, clicking through the profile picker saved
that blank over the user's real settings and switched their sharing off.
Every path the app writes to is now redirected, and isolate() refuses to
start if any of them still points into X:\\NextUp."""
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
    with open(n.CONFIG_PATH, "w", encoding="utf-8") as fh:
        json.dump(n.CONFIG, fh)
    n.RECS_PATH = os.path.join(sandbox, "nextup_recs.json")
    n.PLAY_STATE_PATH = os.path.join(sandbox, "nextup_playing.json")
    n.WATCH_LATER = os.path.join(sandbox, "nextup_resume")
    n.ERROR_LOG = os.path.join(sandbox, "nextup_errors.log")
    for name in ("DB_PATH", "CONFIG_PATH", "RECS_PATH", "PLAY_STATE_PATH",
                 "WATCH_LATER", "ERROR_LOG"):
        path = os.path.abspath(getattr(n, name))
        if path.lower().startswith(live.lower()):
            raise SystemExit("refusing to start: %s still points at %s" % (name, path))


if __name__ == "__main__":
    isolate(nextup, SANDBOX)
    PORT = 8771
    nextup.load_saved_recs()
    print("devserve on http://127.0.0.1:%d (sandbox %s)" % (PORT, SANDBOX), flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), nextup.Handler).serve_forever()
