# Android Shell Implementation Plan (step 3)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A real Next Up APK. It installs on the test phone (Galaxy S21 Ultra, Android 15), starts Next Up's own server inside the app, shows the page full-screen, keeps its data safe across updates, and can see videos in `Movies/Next Up/`.

**Architecture:** A Briefcase/Toga app (`android/`). `app.py` points Next Up's data at the app's private data folder, imports `nextup`, starts its HTTP server on a thread, and opens a Toga `WebView` on `http://127.0.0.1:<port>`. `nextup.py` learns two things: code/assets (`HERE`) and data (`DATA`) can live in different places, and `PLATFORM == "android"` switches off what can't run there.

**Tech Stack:** Briefcase 0.4.5, toga-android ~0.5, Chaquopy (Python 3.14), androidx.webkit. The toolchain is in `X:\DevTools` (see memory). Every Briefcase/Gradle command sets `BRIEFCASE_HOME=X:\DevTools\briefcase-data` and `GRADLE_USER_HOME=X:\DevTools\gradle`.

**Spec:** `docs/superpowers/specs/2026-10-07-android-app-design.md` (Components 2 and 5, build step 3, Unknowns 2–4).

## Global Constraints

- Desktop behaviour is unchanged. With no `NEXTUP_HOME` set, `DATA == HERE`, and every existing path resolves exactly as before. All 10 test suites stay green.
- Data on the phone lives in the app's private data dir (`toga.App.paths.data`). It is never next to the code, which Android replaces on every update.
- Videos are expected in `/storage/emulated/0/Movies/Next Up/` (shared storage, survives reinstalls).
- Bundle id `app.nextup`, app name `nextup`, formal name "Next Up". The id never changes after the first install, or Android treats it as a different app.
- Copies of `nextup.py`, `nextup_fonts/` and `nextup_logo.png` inside `android/src/` are build products. They're gitignored, and the source of truth stays at the repo root.
- Files are written with Unix line endings (`newline="\n"`). The last branch's Windows-ending rewrite must not recur.
- On-device checks use adb from `X:\DevTools\briefcase-data\tools\android_sdk\platform-tools\adb.exe`, launched with `am start --user 0` (the phone has a second user profile). Screenshots go through bash, not PowerShell, which corrupts binary output.

## Review Focus

1. **An app update wipes the library.** If any data path still resolves under `HERE` on Android, an update deletes it. → Task 1 test `every data path is under NEXTUP_HOME`.
2. **The page loads but a desktop-only feature is touched** (the window buttons, mpv, docking drives) and throws, blanking the page. → Task 2 on-device check: no JS errors in logcat (`chromium` tag) and no Python tracebacks, after opening each tab.
3. **The port is taken when the app restarts quickly.** The server must start on a free port, not crash the app. → Task 1 test `serve picks another port when busy`.
4. **The video permission is refused or not asked for.** The library shows empty with no reason. → Task 3: the app says so on screen.
5. **The first launch on the phone has no TMDB key or config.** The page must still render, the same as a fresh desktop install. → Task 2 check on a clean install.

---

### Task 1: nextup.py can run headless, with data elsewhere

**Files:**
- Modify: `nextup.py`: the path constants (lines ~89–99, 1439, 1914, 3031, 3362, 3521, 5812), a new `serve_in_thread()`, and `main()` using it
- Create: `tests/android_core_test.py`; register it in `tests/run_all.py`

**Interfaces:**
- Produces:
  - `DATA = os.environ.get("NEXTUP_HOME") or HERE`. These go under `DATA`: config, cache, dismissed, youtube, phone sync, DB, error log, art, watch-later (resume), play state and recs. Fonts, logo, icon and `MPV_CONFIG_DIR` stay under `HERE`.
  - `PLATFORM = os.environ.get("NEXTUP_PLATFORM") or ("android" if sys.platform == "android" else sys.platform)`.
  - `serve_in_thread(port: int = APP_PORT, host: str = "127.0.0.1") -> int`:
    - binds `ThreadingHTTPServer`, trying `port` and then up to 20 following ports if one is busy;
    - starts it on a daemon thread, along with `sync_loop` and `refresh_watch_scores` (and `playback_monitor` + `adopt_orphan_mpv` only when `PLATFORM != "android"`);
    - returns the port it bound.
    - `main()` keeps its own already-running and port-wait logic, then calls this for the start-up it did inline before.
- [ ] **Step 1: Write the failing tests.** These run a *subprocess* `python -c` with `NEXTUP_HOME=<tmp>` and `NEXTUP_PLATFORM=android`, importing `nextup` and printing JSON. Checks:
  - `every data path is under NEXTUP_HOME`: CONFIG_PATH, DB_PATH, ERROR_LOG, ART_DIR, WATCH_LATER, PLAY_STATE_PATH, RECS_PATH, CACHE_PATH, YOUTUBE_PATH and PHONE_SYNC_DIR all start with tmp
  - `assets stay with the code`: FONTS_DIR and LOGO_PATH start with `X:\NextUp`
  - `PLATFORM is android`
  - `serve answers with the page`: `serve_in_thread(8797)` returns 8797, and GET `/` is 200 and contains `<title>`
  - `serve picks another port when busy`: with 8796 held by a bound socket, `serve_in_thread(8796)` returns 8797 or higher, and that port answers
  - `no player monitor on android`: no thread named like the playback monitor (name it `"playback monitor"` when started)
  - `nothing written beside the code`: the repo root's file list is unchanged by the subprocess
- [ ] **Step 2: Run** `python tests\android_core_test.py`. Expect FAIL (`DATA`/`serve_in_thread` missing).
- [ ] **Step 3: Implement** the Interfaces. Name the playback monitor thread `"playback monitor"`.
- [ ] **Step 4: Run** the test and then `python tests\run_all.py`. Expect all checks to pass, with every suite green.
- [ ] **Step 5: Commit:** `"nextup.py: data apart from code, a headless serve, PLATFORM"`

### Task 2: The app shell, built and running on the phone

**Files:**
- Create:
  - `android/pyproject.toml`
  - `android/src/nextup_app/__init__.py`, `__main__.py` and `app.py`
  - `android/build.py`: copies the sources in with Unix endings, then runs `briefcase create/build android` and `adb install`, with the env vars set
  - `android/.gitignore`: `build/`, `logs/`, and the copied `src/nextup_app/nextup.py`, `nextup_fonts/` and `nextup_logo.png`
- Modify: `.gitignore`, if needed

**Interfaces:**
- Consumes: `serve_in_thread`, `DATA` and `PLATFORM` from Task 1.
- Produces:
  - `pyproject.toml`: bundle `app`, app `nextup`, formal name "Next Up", version from `nextup.APP_VERSION` (hard-coded `0.1.49` for now). Sources `["src/nextup_app"]`, `requires = []`.
  - Android settings:
    - `requires = ["toga-android~=0.5.0"]`;
    - `build_gradle_dependencies` add `androidx.webkit:webkit:1.15.0`;
    - `build_gradle_extra_content` with the `staticProxy("toga_android.widgets.internal.webview")` line;
    - `base_theme = "Theme.MaterialComponents.NoActionBar"`, with no teal title bar.
  - `app.py`:
    - sets `os.environ["NEXTUP_HOME"] = str(self.paths.data)` (and creates it) **before** `import nextup`;
    - `port = nextup.serve_in_thread()`;
    - the main window content is `toga.WebView(url=f"http://127.0.0.1:{port}/")`;
    - any exception during start-up is shown as a `toga.Label` with the traceback instead of a blank screen.
- [ ] **Step 1: Write the check first.** It's an on-device script, `android/check_device.py`, that:
  - installs, then launches with `am start --user 0 -n app.nextup.nextup/org.beeware.android.MainActivity`;
  - waits 8 s, then saves a screenshot with `adb exec-out screencap -p`;
  - dumps `logcat -d`, filtered to `python.stderr`, `AndroidRuntime:E` and `chromium`;
  - exits non-zero if it finds `Traceback`, `FATAL EXCEPTION` or `Uncaught`.
- [ ] **Step 2: Run** `python android\check_device.py` before the app exists. Expect FAIL (package not installed).
- [ ] **Step 3: Implement** the files above. Build with `python android\build.py`.
- [ ] **Step 4: Run** `python android\check_device.py`. Expect exit 0, and a screenshot showing the dark Next Up page (look at it). Then tap through each tab with `adb shell input tap` at the bottom-nav positions read from `uiautomator dump`, or via the page's own tab elements, and run the check again after each. Fix any desktop-only call that throws. (Review Focus 2 and 5: it's a fresh install with no config.)
- [ ] **Step 5: Commit:** `"Android: the app shell — Next Up in a WebView on the phone"`

### Task 3: Seeing videos on the phone (Unknown 2)

**Files:**
- Modify: `android/pyproject.toml` (permissions), `android/src/nextup_app/app.py` (permission request + default media folder), `nextup.py` (if a scan path needs it)

**Interfaces:**
- Produces:
  - Permission `android.permission.READ_MEDIA_VIDEO`, requested at runtime on first launch through Chaquopy's Java bridge (`ActivityCompat.requestPermissions`).
  - On first run, if `media_folders` is empty, app.py sets it to `["/storage/emulated/0/Movies/Next Up"]` and creates the folder.
  - If the permission is refused, the page shows the existing empty-library state, and the Settings media-folders note says Android hasn't given Next Up access to videos.
- [ ] **Step 1: Write the check.** `android/check_storage.py`:
  - pushes a 51 MB sparse test file to `/sdcard/Movies/Next Up/Test Film (2020)/Test Film (2020).mkv` (`adb push`);
  - triggers a scan through the app's own server, using `adb forward tcp:<port>` and then POST `/api/library/scan`;
  - polls `/api/library/status` until it finishes;
  - expects `counts.movies + counts.unmatched >= 1`;
  - removes the test file afterwards.
- [ ] **Step 2: Run** the check. Expect FAIL (0 found, no permission).
- [ ] **Step 3: Implement.** The user taps **Allow** on the permission prompt; that's their decision, and the check waits for it. If file-path access to the shared folder is still refused once allowed, fall back to the spec's alternative (the app's own media folder, `getExternalFilesDir(DIRECTORY_MOVIES)`). Record the outcome as a ledger ruling and in DEVELOPMENT_NOTES.
- [ ] **Step 4: Run** the check. Expect it to find at least one item.
- [ ] **Step 5: Release:**
  - bump `APP_VERSION` and README to 0.1.49;
  - write the DEVELOPMENT_NOTES entry (what was settled for Unknowns 2–4);
  - run `python tests\run_all.py` (all green);
  - commit `"v0.1.49: Next Up runs on Android (shell)"`;
  - uninstall the probe app with `adb uninstall app.nextup.nextupprobe` and delete `X:\DevTools\probe`.
