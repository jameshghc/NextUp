"""Forward the running app's WebView debugging socket to this PC and run
check_page.js against it. The app must be open on the phone (run
check_device.py first). Exit 0 when the page throws nothing."""
import os, re, subprocess, sys

ADB = r"X:\DevTools\briefcase-data\tools\android_sdk\platform-tools\adb.exe"
PACKAGE = "app.nextup.mobile"
PORT = "9223"
HERE = os.path.dirname(os.path.abspath(__file__))


def adb(*args):
    return subprocess.run([ADB] + list(args), capture_output=True, text=True,
                          timeout=60).stdout


pid = adb("shell", "pidof", PACKAGE).strip()
if not pid:
    sys.exit("FAIL  the app isn't running — run check_device.py first")
if "webview_devtools_remote_%s" % pid not in adb("shell", "cat", "/proc/net/unix"):
    sys.exit("FAIL  no WebView debugging socket for the app (release build?)")
adb("forward", "tcp:" + PORT, "localabstract:webview_devtools_remote_" + pid)
try:
    code = subprocess.run(["node", os.path.join(HERE, "check_page.js"), PORT]
                          + sys.argv[1:]).returncode
finally:
    adb("forward", "--remove", "tcp:" + PORT)
sys.exit(code)
