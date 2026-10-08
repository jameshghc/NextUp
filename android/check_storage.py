"""Can Next Up on the phone see videos in Movies/Film & TV/?

Puts a 51 MB dummy film on the phone (over the 50 MB floor the scan uses to
skip samples), asks the app's own server to scan, and passes when the scan
found it. The dummy is removed afterwards either way. The app must be
running (check_device.py)."""
import json, os, subprocess, sys, tempfile, time, urllib.request

ADB = r"X:\DevTools\briefcase-data\tools\android_sdk\platform-tools\adb.exe"
PHONE_DIR = "/sdcard/Movies/Film & TV/Films/Check Film (2020)"
PHONE_FILE = PHONE_DIR + "/Check Film (2020).mkv"
LOCAL_PORT, APP_PORT = 8781, 8770


def adb(*args):
    return subprocess.run([ADB] + list(args), capture_output=True, text=True,
                          timeout=300).stdout


def api(method, path):
    req = urllib.request.Request("http://127.0.0.1:%d%s" % (LOCAL_PORT, path),
                                 data=b"{}" if method == "POST" else None, method=method)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read() or b"{}")


def main():
    dummy = os.path.join(tempfile.gettempdir(), "nextup_check_film.mkv")
    with open(dummy, "wb") as fh:
        fh.truncate(51 * 1024 * 1024)
    # One quoted string: adb hands "shell" its words joined by spaces, to the
    # phone's own shell, and that shell then reads the "&" in "Film & TV" as
    # "run in the background" and the brackets as syntax. Unquoted, the
    # dummy was never removed — twice, before this was noticed.
    adb("shell", "mkdir -p '%s'" % PHONE_DIR)
    adb("push", dummy, PHONE_FILE)
    adb("forward", "tcp:%d" % LOCAL_PORT, "tcp:%d" % APP_PORT)
    try:
        folders = (api("GET", "/api/status").get("config") or {}).get("media_folders")
        print("media folders on the phone: %s" % folders)
        api("POST", "/api/library/scan")
        status = {}
        for _ in range(60):
            time.sleep(1)
            status = api("GET", "/api/library/status")
            if not status.get("running"):
                break
        counts = status.get("counts") or {}
        found = (counts.get("movies") or 0) + (counts.get("unmatched") or 0)
        print("scan: error=%r counts=%s" % (status.get("error"), counts))
        if found >= 1:
            print("PASS  the app sees videos in Movies/Film & TV")
            return 0
        print("FAIL  the scan found nothing")
        return 1
    finally:
        adb("shell", "rm -rf '%s'" % PHONE_DIR)
        adb("forward", "--remove", "tcp:%d" % LOCAL_PORT)
        os.remove(dummy)


if __name__ == "__main__":
    sys.exit(main())
