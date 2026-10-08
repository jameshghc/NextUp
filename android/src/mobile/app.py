"""Next Up on Android: the app's own server, shown full-screen.

Everything the desktop app is, minus its window: nextup.py runs its HTTP
server on a thread inside this app, and a WebView shows the page. Its data
— library, settings, posters — goes in this app's private data folder,
never beside the code, which Android replaces whenever the app updates.
"""
import os
import threading
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
            nextup.ANDROID_PLAYER = lambda path, start: open_in_player(self, path, start)
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
# mpv for Android, from the Play Store.
MPV_PACKAGE = "is.xyz.mpv"


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


def open_in_player(app, path, start):
    """Play a file in the mpv app, `start` seconds in.

    Another app can't be handed a plain file path on Android — it has to be
    the file's entry in Android's own media index, lent with permission to
    read it. If mpv isn't installed (or won't take it), Android's "open
    with" list instead, so pressing play always opens something."""
    from java import jclass, jint
    Intent = jclass("android.content.Intent")
    NotFound = jclass("android.content.ActivityNotFoundException")
    activity = app._impl.native
    intent = Intent(Intent.ACTION_VIEW)
    intent.setDataAndType(media_uri(activity, path), "video/*")
    intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    if start > 5:
        # mpv's own name for it, in milliseconds — the one MX Player uses.
        intent.putExtra("position", jint(start * 1000))
    intent.setPackage(MPV_PACKAGE)
    try:
        activity.startActivity(intent)
    except NotFound:
        intent.setPackage(None)
        activity.startActivity(Intent.createChooser(intent, "Play with"))


def media_uri(activity, path):
    """The file's content:// address in Android's media index. A file the
    PC has just copied over isn't in the index yet — adb doesn't tell it —
    so then Android is asked to look at it, and that answer is waited for."""
    from java import jclass, dynamic_proxy
    Media = jclass("android.provider.MediaStore$Video$Media")
    ContentUris = jclass("android.content.ContentUris")
    cursor = activity.getContentResolver().query(
        Media.EXTERNAL_CONTENT_URI, ["_id"], "_data=?", [path], None)
    if cursor is not None:
        try:
            if cursor.moveToFirst():
                return ContentUris.withAppendedId(Media.EXTERNAL_CONTENT_URI, cursor.getLong(0))
        finally:
            cursor.close()

    Scanner = jclass("android.media.MediaScannerConnection")
    Listener = jclass("android.media.MediaScannerConnection$OnScanCompletedListener")
    found, done = [None], threading.Event()

    class Scanned(dynamic_proxy(Listener)):
        def onScanCompleted(self, scanned, uri):
            found[0] = uri
            done.set()

    Scanner.scanFile(activity, [path], None, Scanned())
    done.wait(20)
    if found[0] is None:
        raise RuntimeError("Android hasn't added %s to its list of videos yet — "
                           "try again in a moment." % os.path.basename(path))
    return found[0]


def main():
    return NextUp()
