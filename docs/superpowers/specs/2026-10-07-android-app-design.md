# Next Up on Android: design

**Date:** 2026-10-07 · **Status:** approved in conversation, awaiting review of this write-up
**Device:** Samsung Galaxy S24 Ultra, 1 TB, One UI on Android 14+

## Goal

A separate Next Up app on the phone, on the model of the MacBook copy: its
own library of what's stored **on the phone**, with everything on the PC
visible beside it, populated by the main Windows app. Opening it should
just work: tap the icon, the library is there, things play.

**Success looks like:**

1. Tap the icon and Next Up opens. No Termux, no browser, no start-up step.
2. Films and episodes stored on the phone play, offline, anywhere.
3. Everything on the PC appears too, marked as on the PC, and can be
   downloaded to the phone in one tap on home Wi-Fi.
4. Ratings, history, watchlist, favourites and resume points flow between
   phone and PC on their own whenever both are on home Wi-Fi.
5. Resume, "watched it" and the Watch Score work for what's watched on the
   phone, just as they do on the PC.

**Out of scope:** watching away from home *from the PC's drives*
(streaming, tunnels); Play Store publishing; the docking station, the
download sorter, drive detection and the remote on the phone; transcoding.

## Decisions taken

| Question | Decision | Why |
|---|---|---|
| What the phone is | A separate app with its own library, like the Mac | the user's call |
| Where its videos come from | Stored on the phone (1 TB) | the user's call; works offline |
| How it runs | A real APK built with **BeeWare Briefcase**, with Python inside the app and the page shown in a WebView | "open the app and it works"; Termux would need starting and can't hear back from the player |
| How it plays | Hands the file to the **mpv** Android app (VLC as fallback) and reads back the position | .mkv is ~80% of the library and no WebView plays it |
| How it gets the PC's library, and syncs | **Directly from the PC over home Wi-Fi**, paired once with a code | OneDrive on Android keeps no real folder, so the cloud-folder sync the Mac uses can't work on the phone |
| How films get onto it | **Downloaded from the PC over Wi-Fi**, from inside the app | over USB the phone has no drive letter, so the docking station can't reach it |

Ruled out: Termux (needs starting, no position back), a native rewrite
(two apps to keep forever), a page served by the PC (not a separate app,
and nothing works away from home).

## What makes this tractable

`nextup.py` uses only the Python standard library apart from `webview`
(pywebview, the desktop window). That's checked: 32 stdlib modules, one
third-party one. On Android, Next Up's own HTTP server runs on a thread
inside the app and an Android WebView loads `http://127.0.0.1:<port>`.
Everything server-side runs as it does on the PC.

## Components

### 1. PC side: letting the phone in (built and tested first)

Today the server binds `127.0.0.1` and has no authentication, and some
routes move files to the Recycle Bin. Before anything else:

- **LAN listener, off by default.** A second listener on the PC's
  home-network address, turned on from Settings ("Let a phone connect"),
  on its own port (8790). The existing `127.0.0.1` server is unchanged.
- **Pairing.** Settings shows a 4-digit code that's valid for five
  minutes. The phone sends it and gets back a long random token. The PC
  stores the token against the device's name, and Settings lists paired
  phones with FORGET.
- **Every LAN request carries the token**, or it's refused. Anything not on
  an allow-list is refused even with a token: the bin, settings, the
  sorter, the docking station, mpv control and library scans.
- **Phone routes, and nothing else on the LAN listener:**
  - `GET  /phone/snapshot`: `build_library_snapshot()`, plus for each item
    a file reference (a stable key: tmdb id, or show tmdb id + season +
    episode, and the extension) so the phone can ask for the file. No sizes:
    stat-ing ~3,000 files on E: is the drive-stall risk the app already
    guards against. The phone reads the size from the download's
    Content-Length before committing space.
  - `GET  /phone/file?key=…`: streams the file, honouring `Range` so an
    interrupted download resumes. Only files the library knows can be
    asked for, so no path ever comes from the phone.
  - `GET  /phone/sync` / `POST /phone/sync`: the phone fetches the PC's
    event file and hands over its own (see 4).
  - `GET  /phone/art/…`: posters the phone hasn't got.
- **Found automatically.** The PC answers a UDP broadcast on the home
  network with its name and port, so the phone finds it without anyone
  typing an IP address. Typing one in remains as a fallback.

### 2. The Android app shell

- A **Briefcase** project in `android/`. Its `app.py` imports `nextup`,
  starts the server on a thread and opens a WebView on it.
- **`PLATFORM = "android"`** in `nextup.py`, decided at start-up, switches
  off what can't work there:
  - the docking station, the sorter, drive detection and the remote;
  - mpv IPC and keep-open channels: channels still schedule, and tuning
    in hands that one programme to the player.
- **Where things live:** the database, config and art go in the app's
  private storage. Videos go in `Movies/Next Up/` on shared storage, so
  they survive reinstalling the app and the user can see them in My Files.
- **Permissions:** whatever Android needs to read and write that folder.
  This is checked on the device in step 3; see Unknowns.

### 3. Playback on the phone

- PLAY sends an Android intent to **mpv** (`is.xyz.mpv`) with the file and
  a start position, using Chaquopy's Java bridge. When mpv returns, the
  position and duration it reports go through the same
  `note_playback_finished` the PC uses, so resume, watched, history and
  the Watch Score all behave the same.
- **If mpv doesn't report a position** (to check early), the fallback is
  **VLC**, whose result extras (`extra_position`, `extra_duration`) are
  documented. Failing both, Next Up asks "finished it?" when you come back.
- Neither player installed: a message with a button that opens the Play
  Store on mpv.

### 4. Sync over Wi-Fi

The existing sync model carries over unchanged. Each device appends only
to its own event file, events are keyed by TMDB id, de-duplicated by uid,
and the later UTC time wins. Only the transport is new:

- The phone keeps a local mirror of a sync folder. On home Wi-Fi it
  downloads the PC's device file into the mirror, runs the existing
  `sync_import` / `sync_apply` on it, then uploads its own device file,
  which the PC drops into its own local sync folder and imports the same
  way.
- That works whether or not OneDrive sharing is on at the PC. When it is,
  the phone's events reach the Mac through the PC as well.
- **Import rule (from the v0.1.48 review):** the PC's `GET /phone/sync`
  body is rebuilt fresh each time and is *not* append-only. Seeds come
  first, and relayed events are ordered by time, so new lines can land
  anywhere. The phone must import it **from offset 0 every time** (clear
  its `sync_files` row first). uids make re-reading harmless, but resuming
  from the old offset would skip events. The phone's own file must stay
  append-only, because in cloud mode the Mac reads it by offset.
- **When it runs:** on opening the app, when it returns to the
  foreground, and every five minutes while open on home Wi-Fi.
- **Rules that must still hold** (from v0.1.22): applying an event never
  calls `log_event`, and a remote resume position must be written where
  the player's resume will find it.

### 5. Library on the phone

- **"On this phone":** the files in `Movies/Next Up/`, scanned and matched
  as on the PC. Downloaded files are named so they match first time:
  `Title (Year).ext`, or `Show/Season NN/SxxEyy - Show.ext`.
- **"On the PC":** the snapshot, through the existing `elsewhere` display
  ("ON <PC NAME>" badge). These rows gain **DOWNLOAD TO PHONE**. Shows
  offer the next N unwatched episodes or a season.
- **Downloads:** a queue with a progress bar and resume after a break.
  Before starting it checks free space and says if there isn't room.
- **Deleting from the phone:** asked every time; it removes the phone's
  copy only, and the item reverts to "on the PC".

### 6. The phone layout

The page targets a 760px+ window; the S24 Ultra is ~412 CSS px wide. A
responsive pass, in a phone-only block at the end of the stylesheet, so
the desktop layout is untouched:

- bottom navigation (Now / Library / Rate / Channels / ⚙);
- tiles two or three across;
- sheets go full-screen;
- touch targets of at least 44px;
- no hover-only information (the tile peek becomes a tap).

## Error handling

- **PC not reachable:** the phone works on what it has. A quiet line says
  when it last synced, and nothing nags.
- **Download fails part way:** it resumes from the last byte via `Range`.
  If the file has gone from the PC, it says so.
- **Pairing refused or token revoked:** the phone says so and offers to
  pair again.
- **Low storage:** checked before a download starts, never part way.

## Testing

- **PC side** (`tests/phone_link_test.py`): pairing code expiry, token
  required, allow-list enforced (the bin, settings and so on refused even
  with a token), `/phone/file` serves only known files, honours `Range`
  and resumes, snapshot keys round-trip, sync exchange through the
  existing apply path. All sandboxed by `devserve.isolate`, with no real
  network beyond localhost.
- **Phone-side logic** runs on the PC too, with `PLATFORM` forced to
  `android`: Windows-only routes off, download naming matches the scanner,
  sync over a fake PC.
- **On the device**, with USB debugging: install with `adb`, read the
  app's log, and take screenshots with `adb exec-out screencap` to verify
  without the user. Real checks: launch, pair, download one film, play it
  in mpv, stop part way, confirm the resume point and that it reaches the
  PC.

## Build order

| Step | Work | Needs the user |
|---|---|---|
| 1 | PC side: LAN listener, pairing, allow-list, phone routes, discovery; tests | no |
| 2 | Android toolchain on the PC: JDK, Android SDK, Briefcase (~5 GB) | approve downloads |
| 3 | First APK: shell starts the server, WebView shows the page; settle permissions and Python version | USB debugging on once, approve install |
| 4 | Pairing, snapshot, downloads, sync on the device | tap through pairing |
| 5 | Playback via mpv/VLC, with position coming back | install mpv from the Play Store |
| 6 | Phone layout pass, then polish | use it, report what grates |

## Unknowns, each settled before anything leans on it

1. **Does mpv-android return the position?** Checked in step 5 before
   building around it. VLC's documented result is the fallback.
2. **Storage permission on One UI / Android 14+** for a shared
   `Movies/Next Up/` folder. Checked in step 3. The fallback is the app's
   own media folder, which needs no permission, at the cost of being
   removed when the app is uninstalled.
3. **Python version.** `nextup.py` is verified on 3.14. Briefcase's
   Android support (via Chaquopy) may top out lower. Checked in step 3:
   any 3.14-only syntax gets made compatible.
4. **WebView and the page.** The page is plain HTML and JS with
   self-hosted fonts, so it's expected to work. Confirmed on first launch.

## Updating the app

At first, new builds are installed with `adb` over USB. Later the PC
can offer the phone its latest APK at pairing time, and the phone can
install it after the user taps through Android's prompt. That isn't
needed for a first version.
