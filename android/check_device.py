"""Is Next Up running on the phone, and running cleanly?

Launches the installed app on the USB-connected phone, waits for it to
settle, saves a screenshot to android/check/screen.png, and reads the
phone's log for the three ways it goes wrong: a Python traceback, an
Android crash, or an uncaught error in the page's own javascript.

    python android\\check_device.py          launch, screenshot, check
    python android\\check_device.py --no-launch   check what's on screen now

Exit 0 when clean. Needs USB debugging on and the phone unlocked."""
import os, re, subprocess, sys, time

ADB = r"X:\DevTools\briefcase-data\tools\android_sdk\platform-tools\adb.exe"
PACKAGE = "app.nextup.mobile"
ACTIVITY = PACKAGE + "/org.beeware.android.MainActivity"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "check")
BAD = re.compile(r"Traceback|FATAL EXCEPTION|Uncaught")


def adb(*args, binary=False):
    out = subprocess.run([ADB] + list(args), capture_output=True, timeout=60)
    return out.stdout if binary else out.stdout.decode("utf-8", "replace")


def main():
    os.makedirs(OUT, exist_ok=True)
    # The exact line, not a substring: one id can be the start of another.
    listed = adb("shell", "pm", "list", "packages", "--user", "0", PACKAGE).split()
    if "package:" + PACKAGE not in listed:
        print("FAIL  %s isn't installed on the phone" % PACKAGE)
        return 1
    if "--no-launch" not in sys.argv:
        adb("logcat", "-c")
        adb("shell", "am", "force-stop", PACKAGE)
        adb("shell", "am", "start", "--user", "0", "-n", ACTIVITY)
        time.sleep(8)
    if "isKeyguardShowing=true" in adb("shell", "dumpsys", "window"):
        print("FAIL  the phone is locked — unlock it and run again")
        return 1
    with open(os.path.join(OUT, "screen.png"), "wb") as fh:
        fh.write(adb("exec-out", "screencap", "-p", binary=True))
    log = adb("logcat", "-d", "-v", "brief",
              "python.stdout:I", "python.stderr:*", "AndroidRuntime:E", "chromium:*", "*:S")
    with open(os.path.join(OUT, "logcat.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(log)
    problems = [l for l in log.splitlines() if BAD.search(l)]
    running = bool(adb("shell", "pidof", PACKAGE).strip())
    print("screenshot: %s" % os.path.join(OUT, "screen.png"))
    if not running:
        print("FAIL  the app isn't running (crashed?)")
    for line in problems[:20]:
        print("FAIL  " + line)
    if running and not problems:
        print("PASS  running, no tracebacks, crashes or uncaught page errors")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
