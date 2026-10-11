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
            nextup.ANDROID_PLAYER = lambda path, start, subs=None: open_in_player(
                self, nextup, path, start, subs)
            first_run_library(nextup)
            name_the_phone(self, nextup)
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
        handle_back(self)
        pause_with_app(self)
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
# mpv for Android, from the Play Store, and what it calls its answer.
MPV_PACKAGE = "is.xyz.mpv"
MPV_RESULT = "is.xyz.mpv.MPVActivity.result"


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


def name_the_phone(app, nextup):
    """What the phone is called — Android's own name for it, "James's S24
    Ultra" — rather than "localhost", which is all its hostname says. It's
    on the profile screen, and it's how the PC lists the phone among the
    devices it shares history with. Left alone once set, so renaming it in
    Next Up sticks."""
    if (nextup.CONFIG.get("device_name") or "").strip():
        return
    try:
        from java import jclass
        Global = jclass("android.provider.Settings$Global")
        Build = jclass("android.os.Build")
        name = Global.getString(app._impl.native.getContentResolver(), "device_name") or Build.MODEL
        if name:
            nextup.CONFIG["device_name"] = str(name)[:40]
            nextup.save_json(nextup.CONFIG_PATH, nextup.CONFIG)
    except Exception:
        traceback.print_exc()   # it'll just be "localhost"


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
    full_screen(app)


def full_screen(app):
    """More of the screen for Next Up: the clock-and-notifications bar
    hidden while it's open (a swipe in from the edge shows it for a
    moment), and the page allowed beside the camera instead of a grey strip
    there in landscape. The navigation bar stays in portrait, where it's
    wanted, and goes in landscape, where it cut the page off — see
    fit_bars, which runs again whenever the phone turns."""
    try:
        from java import jclass
        WindowCompat = jclass("androidx.core.view.WindowCompat")
        Controller = jclass("androidx.core.view.WindowInsetsControllerCompat")
        Types = jclass("androidx.core.view.WindowInsetsCompat$Type")
        Params = jclass("android.view.WindowManager$LayoutParams")
        window = app._impl.native.getWindow()
        WindowCompat.setDecorFitsSystemWindows(window, False)
        attrs = window.getAttributes()
        attrs.layoutInDisplayCutoutMode = Params.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
        window.setAttributes(attrs)
        fit_bars(app)
        no_margins(app)
        follow_turns(app)
    except Exception:
        traceback.print_exc()


def fit_bars(app):
    """Status bar hidden always; navigation bar hidden in landscape only."""
    from java import jclass
    Controller = jclass("androidx.core.view.WindowInsetsControllerCompat")
    Types = jclass("androidx.core.view.WindowInsetsCompat$Type")
    Configuration = jclass("android.content.res.Configuration")
    activity = app._impl.native
    window = activity.getWindow()
    bars = Controller(window, window.getDecorView())
    bars.setSystemBarsBehavior(Controller.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE)
    bars.hide(Types.statusBars())
    if activity.getResources().getConfiguration().orientation == Configuration.ORIENTATION_LANDSCAPE:
        bars.hide(Types.navigationBars())
    else:
        bars.show(Types.navigationBars())


def follow_turns(app):
    """fit_bars again every time the phone is turned. The app handles
    turning itself (the manifest says so) rather than being restarted, so
    Android tells it through these callbacks instead."""
    from java import jclass, dynamic_proxy
    Callbacks = jclass("android.content.ComponentCallbacks")

    class Turned(dynamic_proxy(Callbacks)):
        def onConfigurationChanged(self, config):
            try:
                fit_bars(app)
            except Exception:
                traceback.print_exc()

        def onLowMemory(self):
            pass

    _KEEP.append(Turned())
    app._impl.native.registerComponentCallbacks(_KEEP[-1])


def no_margins(app):
    """Briefcase's launcher keeps the page clear of the bars AND the camera
    cutout by giving it margins, which in landscape left a strip down the
    camera end even with the status bar hidden. Its handler sits on the
    page itself, which the app replaces after this runs — so the answer is
    given one level up instead: the container the page sits in passes on no
    status bar, and the launcher's own handler then keeps only the margins
    still wanted. A status bar swiped in for a moment floats over the page.

    The camera: in landscape the page runs beside it, as the user asked —
    it's only a small hole at the edge of a wide screen. In portrait it sat
    in the middle of the top bar, over the version and the counts, so there
    the page starts below it (on a strip the page's own colour)."""
    from java import jclass, dynamic_proxy
    Listener = jclass("androidx.core.view.OnApplyWindowInsetsListener")
    ViewCompat = jclass("androidx.core.view.ViewCompat")
    Builder = jclass("androidx.core.view.WindowInsetsCompat$Builder")
    Types = jclass("androidx.core.view.WindowInsetsCompat$Type")
    Insets = jclass("androidx.core.graphics.Insets")
    Configuration = jclass("android.content.res.Configuration")
    activity = app._impl.native
    content = activity.findViewById(jclass("android.R$id").content)

    class Edge(dynamic_proxy(Listener)):
        def onApplyWindowInsets(self, view, insets):
            landscape = (activity.getResources().getConfiguration().orientation
                         == Configuration.ORIENTATION_LANDSCAPE)
            edges = Types.statusBars() | (Types.displayCutout() if landscape else 0)
            return Builder(insets).setInsets(edges, Insets.NONE).build()

    ViewCompat.setOnApplyWindowInsetsListener(content, Edge())
    ViewCompat.requestApplyInsets(content)


def pause_with_app(app):
    """When Next Up goes into the background — the home button, another app,
    mpv playing a film — its web view is paused too, page timers and all,
    and started again when it comes back. Toga doesn't do this itself, so a
    page left open in the background went on waking the phone."""
    try:
        webview = app.main_window.content._impl.native
        cls = type(app._impl._listener)
        paused, resumed = cls.onPause, cls.onResume

        def onPause(self):
            paused(self)
            try:
                webview.onPause()
                webview.pauseTimers()
            except Exception:
                traceback.print_exc()

        def onResume(self):
            try:
                webview.resumeTimers()
                webview.onResume()
            except Exception:
                traceback.print_exc()
            resumed(self)

        cls.onPause, cls.onResume = onPause, onResume
    except Exception:
        traceback.print_exc()   # the app works without it, just less frugally


def handle_back(app):
    """Back closes what's open in the page first — a film's details, say —
    and only from the bare page does it leave, by going to the background
    rather than quitting, as Android apps do. The page is asked
    (nextupBack, in nextup.py) because only it knows what's open.

    Android's own Back callback (13 and later), which the manifest opts in
    to — see pyproject.toml."""
    try:
        from java import jclass, dynamic_proxy
        Callback = jclass("android.window.OnBackInvokedCallback")
        Dispatcher = jclass("android.window.OnBackInvokedDispatcher")
        ValueCallback = jclass("android.webkit.ValueCallback")
        activity = app._impl.native
        webview = app.main_window.content._impl.native

        class Answer(dynamic_proxy(ValueCallback)):
            def onReceiveValue(self, value):
                if str(value) != "true":
                    activity.moveTaskToBack(True)

        class OnBack(dynamic_proxy(Callback)):
            def onBackInvoked(self):
                webview.evaluateJavascript(
                    "typeof nextupBack === 'function' && nextupBack()", Answer())

        _KEEP.append(OnBack())      # Android holds it weakly enough to lose it
        activity.getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
            Dispatcher.PRIORITY_DEFAULT, _KEEP[-1])
    except Exception:
        traceback.print_exc()   # Back then just leaves, as it did before


_KEEP = []


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


def open_in_player(app, nextup, path, start, subs=None):
    """Play a file in the mpv app, `start` seconds in, and when it closes
    tell nextup where it got to.

    A path that's a web address is the PC streaming over the Wi-Fi: mpv is
    given the address as it is, with the subtitle files' addresses beside
    it, since there's no file here for Android to lend.

    Another app can't be handed a plain file path on Android — it has to be
    the file's entry in Android's own media index, lent with permission to
    read it. If mpv isn't installed (or won't take it), Android's "open
    with" list instead, so pressing play always opens something."""
    from java import jarray, jclass, jint
    Intent = jclass("android.content.Intent")
    NotFound = jclass("android.content.ActivityNotFoundException")
    intent = Intent(Intent.ACTION_VIEW)
    if path.startswith("http"):
        Uri = jclass("android.net.Uri")
        intent.setDataAndType(Uri.parse(path), "video/*")
        if subs:
            # mpv's own extras: every subtitle on offer, and which to show.
            intent.putExtra("subs", jarray(Uri)([Uri.parse(x) for x in subs]))
            intent.putExtra("subs.enable", jarray(Uri)([Uri.parse(subs[0])]))
    else:
        intent.setDataAndType(media_uri(app._impl.native, path), "video/*")
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    if start > 5:
        # mpv's own name for it, in milliseconds — the one MX Player uses.
        intent.putExtra("position", jint(int(start * 1000)))
    intent.setPackage(MPV_PACKAGE)

    def closed(code, data):
        try:
            nextup.android_play_finished(**player_report(code, data))
        except Exception:
            traceback.print_exc()

    started, failed = threading.Event(), []

    def launch():
        # Started "for a result": that's what has Android hand back what mpv
        # says as it closes. On the app's own thread, where Android expects it.
        try:
            try:
                app._impl.start_activity(intent, on_complete=closed)
            except NotFound:
                intent.setPackage(None)
                app._impl.start_activity(Intent.createChooser(intent, "Play with"),
                                         on_complete=closed)
        except Exception as exc:
            failed.append(exc)
        finally:
            started.set()

    app.loop.call_soon_threadsafe(launch)
    started.wait(10)
    if failed:
        raise failed[0]


def player_report(code, data):
    """What mpv hands back as it closes: where it stopped and the file's
    length, in milliseconds, when you back out part way. When the file runs
    to the end it closes with a plain OK and no position — that's the end.
    Another player, or a cancelled one, hands back nothing usable, which
    records nothing."""
    RESULT_OK = -1
    extras = data.getExtras() if data is not None else None
    position = extras.getInt("position", -1) if extras is not None else -1
    duration = extras.getInt("duration", -1) if extras is not None else -1
    if position >= 0 and duration > 0:
        return {"position": position / 1000.0, "duration": duration / 1000.0}
    if code == RESULT_OK and data is not None and data.getAction() == MPV_RESULT:
        return {"completed": True}
    return {}


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
