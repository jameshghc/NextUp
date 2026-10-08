"""Next Up on Android: the app's own server, shown full-screen.

Everything the desktop app is, minus its window: nextup.py runs its HTTP
server on a thread inside this app, and a WebView shows the page. Its data
— library, settings, posters — goes in this app's private data folder,
never beside the code, which Android replaces whenever the app updates.
"""
import os
import traceback

import toga


class NextUp(toga.App):
    def startup(self):
        self.main_window = toga.MainWindow(title=self.formal_name)
        try:
            data = str(self.paths.data)
            os.makedirs(data, exist_ok=True)
            # Read by nextup.py as it's imported, so it has to be set first.
            os.environ["NEXTUP_HOME"] = data
            import nextup
            nextup.ANDROID_VIDEO_ACCESS = lambda: has_video_access(self)
            first_run_library(nextup)
            port = nextup.serve_in_thread()
            self.main_window.content = toga.WebView(
                url="http://127.0.0.1:%d/" % port, style=toga.style.Pack(flex=1))
        except Exception:
            # A blank white screen says nothing. The reason, on screen, says
            # what to fix.
            self.main_window.content = toga.Label(
                "Next Up couldn't start:\n\n" + traceback.format_exc())
        self.main_window.show()
        dark_bars(self)
        ask_for_videos(self)


# Where films live on the phone: the user's own Film & TV folder in shared
# storage (Films/ and TV/ inside), so they outlast the app being reinstalled
# and show up in My Files like any other video.
PHONE_LIBRARY = "/storage/emulated/0/Movies/Film & TV"
# The first builds' default, swapped for the folder above wherever it's
# still the only one set.
OLD_DEFAULT = "/storage/emulated/0/Movies/Next Up"
# Next Up's near-black, for the phone's own status and navigation bars so
# they don't frame the page in Android's default teal and white.
INK = "#060509"
VIDEO_PERMISSION = "android.permission.READ_MEDIA_VIDEO"


def first_run_library(nextup):
    """A fresh install has no media folders. On a phone there is only one
    sensible answer, so it's set rather than asked for."""
    if nextup.CONFIG.get("media_folders") not in (None, [], [OLD_DEFAULT]):
        return
    try:
        os.makedirs(PHONE_LIBRARY, exist_ok=True)
    except OSError:
        pass                    # created later, once access is granted
    nextup.CONFIG["media_folders"] = [PHONE_LIBRARY]
    nextup.save_json(nextup.CONFIG_PATH, nextup.CONFIG)


def dark_bars(app):
    """The status bar and the navigation bar in the page's own colour, with
    light icons on them. Set at run time: Briefcase's theme settings reach
    the status bar but not the navigation bar."""
    try:
        from java import jclass
        Color = jclass("android.graphics.Color")
        Controller = jclass("androidx.core.view.WindowInsetsControllerCompat")
        window = app._impl.native.getWindow()
        ink = Color.parseColor(INK)
        window.setStatusBarColor(ink)
        window.setNavigationBarColor(ink)
        bars = Controller(window, window.getDecorView())
        bars.setAppearanceLightStatusBars(False)
        bars.setAppearanceLightNavigationBars(False)
    except Exception:
        traceback.print_exc()   # cosmetic: the app works without it


def has_video_access(app):
    """Asked by nextup.py's status route, so a refusal is said on screen
    rather than looking like an empty phone. Cheap enough to ask each time,
    which also means allowing it later in Android's settings just works."""
    try:
        from java import jclass
        ContextCompat = jclass("androidx.core.content.ContextCompat")
        PackageManager = jclass("android.content.pm.PackageManager")
        return ContextCompat.checkSelfPermission(app._impl.native, VIDEO_PERMISSION) \
            == PackageManager.PERMISSION_GRANTED
    except Exception:
        traceback.print_exc()
        return True             # can't tell: don't claim a refusal that may not be


def ask_for_videos(app):
    """Android's own prompt for reading the phone's videos, once. Without it
    the library folder reads as empty, which looks like nothing is there."""
    try:
        from java import jclass
        ContextCompat = jclass("androidx.core.content.ContextCompat")
        ActivityCompat = jclass("androidx.core.app.ActivityCompat")
        PackageManager = jclass("android.content.pm.PackageManager")
        activity = app._impl.native
        granted = ContextCompat.checkSelfPermission(activity, VIDEO_PERMISSION)
        if granted != PackageManager.PERMISSION_GRANTED:
            ActivityCompat.requestPermissions(activity, [VIDEO_PERMISSION], 1)
    except Exception:
        traceback.print_exc()   # shows in the phone's log; the app carries on


def main():
    return NextUp()
