# Development Notes

Running log of substantial work sessions on Next Up. Newest entries at the top,
with what's still to do at the very top of all.

---

# Planned

Moved out to its own file: see **PLANNED.md** in this folder. It holds the
Mac update, the phone idea, the archive prune, the X-Men '97 duplicate and
the launcher notes, most pressing first.

This file stays what it always was: the record of what has been done, newest
at the top.

---

## 2026-10-09 — v0.1.57, the library on a phone held sideways

A phone in landscape is ~853x384, past the 600px phone rules, so it got
the PC's library: search row and pager fixed, one row of four 187px
posters between, and the pager alone ~30px of the 384. Under
`@media (orientation:landscape) and (max-height:520px)`, `body.android`
only: #view-library scrolls as one (#tiles-out no longer its own scroll
box), so the pager follows the last poster and the search row scrolls away;
posters repeat(6) — six across on any phone (seven, by size, was too many). PREV/NEXT now also zero both
#tiles-out and #view-library's scrollTop, so a new page starts at its top
whichever box scrolls. Portrait unchanged (checked in phone_serve at
384x853 and 853x384, then on the S21).

## 2026-10-09 — v0.1.56, the phone app full-screen, with Back and swipe-down

From the user on the S21 and S24U.

- **Full screen** (app.py `full_screen`): the status bar hidden (a swipe
  down shows it for a moment) — the navigation bar too at first, but the
  user wanted Samsung's back/home/recents kept, so it stays in portrait;
  in landscape it cut the page off, so there it's hidden too (`fit_bars`,
  re-run on every turn through a ComponentCallbacks registered on the
  activity — the manifest has the app handle orientation itself, so it
  isn't restarted). Only statusBars + displayCutout are zeroed below — and `layoutInDisplayCutoutMode =
  SHORT_EDGES`. That alone left a 75px strip at the camera end in
  landscape: Briefcase's MainActivity gives the page MARGINS for system
  bars + display cutout, from a listener on the page view — which toga
  replaces after startup, taking a listener set there with it. `no_margins`
  answers one level up instead, on android.R.id.content, passing on insets
  with systemBars and displayCutout zeroed; Briefcase's listener then sets
  0 margins.
- **Back** closes what's open before leaving. The page's `nextupBack()`
  closes the tile menu, the top `.sheet`, or the queue overlay and returns
  true, or returns false. app.py's `handle_back` registers an
  OnBackInvokedCallback (an interface, so a dynamic proxy), asks the page
  via evaluateJavascript, and on false does `moveTaskToBack(true)` — the
  background, not a quit. Needs `android:enableOnBackInvokedCallback="true"`
  (pyproject: `android_manifest_application_attrs_extra_content`).
  androidx's OnBackPressedCallback was tried first: Chaquopy's static
  proxy can't call its one-argument constructor, so it won't compile.
- **The top strip over the details.** `#titlebar` is z-index 80, above a
  `.sheet` (50) — right on the PC, where it holds the window buttons. On
  Android, `/` is served with `<body class="android">`, and
  `body.android .sheet{z-index:85}`.
- **Swipe down to close** a detail sheet (`sheetSwipe`): from the panel's
  top only, follows the finger, closes past 120px, springs back otherwise.
- Verified on the S21 (Android 15): no strip, Back closes the details
  then backgrounds the app, the scrolled sheet covers the strip, a swipe
  down closes it.

## 2026-10-09 — v0.1.55 (cont.), a film finished on the phone counts as watched

Reading mpv-android's own source (MPVActivity.kt) for the audio-delay
question turned up a mistake in v0.1.54: it sends no `end_by` at all. Back
press gives `position` and `duration` (ms); a file that runs out closes
through its shutdown path with RESULT_OK, action
`is.xyz.mpv.MPVActivity.result`, and no time extras. `player_report` now
reads that as the end. `android_play_finished` ignores an "end" within
MIN_WATCH_SECONDS of opening, since a file mpv can't play closes the same
way.

Also learned, for the audio delay: mpv-android reads `decode_mode`, `subs`,
`subs.enable`, `position`, `title` and `filepath` — no audio delay. It does
turn a content:// into the real path, so `use-filedir-conf` was a thought,
but it holds only READ_MEDIA_* permissions and a .conf isn't media: scoped
storage won't let it read one. Delay on the phone needs a player of our own.

## 2026-10-09 — v0.1.55, audio delay remembered per film and episode

The user fixes a lot of downloads by -100ms on the remote, every time.
Now it's set once per file and put back whenever that file plays.

- `audio_delay` (ms) on movies and episodes, via LATER_COLUMNS.
- `note_audio_delay()` saves what mpv is using for the item playing. Called
  by the remote's delay route at once, and by the monitor each tick once
  the file has settled, so mpv's own Ctrl+/Ctrl- count too. Writes only on
  a change, and only when mpv's `path` is the item's own file: while one
  file replaces another the app still has the old one down as playing.
- Put back on every load: `--audio-delay` for a new player, and the
  `audio-delay` per-file option on loadfile (set_property in the old-mpv
  fallback). Always sent, 0 when nothing is saved. That also fixes a delay
  set for one episode following you into every file after it in the same
  window, which it did before — audio-delay is global in mpv.
- Not on the phone: mpv-android takes no audio delay in what it's handed.
- tests/audio_delay_test.py (10), in run_all.

## 2026-10-09 — v0.1.54, the phone remembers where you got to, and has your ratings

Two things the user found on the S24U, and a way to see the phone's
behaviour without one.

**Where you got to.** On the PC, PLAY with no position still resumes,
because mpv's own watch-later file does it. The phone's mpv keeps none for
us, and nothing came back when it closed, so every PLAY started at 0.

- `/api/play` on Android starts at `resume_position()` when not told
  otherwise — what mpv on the PC does by itself.
- `open_in_player` now starts mpv *for a result* (`app._impl.start_activity`
  with `on_complete`, on the app's own loop). mpv hands back `position` and
  `duration` in ms on leaving part way, or `end_by=playback_completion` at
  the end (the MX Player convention); `player_report` reads that and calls
  `nextup.android_play_finished`.
- `android_play_finished` records it exactly as a PC sitting:
  `note_playback_finished` (resume point, or watched past 97%), or
  `_record_play` at the end. `note_now_playing` keeps the sitting in
  `_ANDROID_SITTING` for it. A report with nothing sitting does nothing.

**Ratings.** The snapshot carries them, but its rows only stand in for
films the phone hasn't got. Every film on the phone is shown from the
phone's own scan, unrated — so the ratings went nowhere that mattered.
`adopt_snapshot_marks()` copies rating (and rated_at) and playcount across
by TMDB id, only where the phone has none, with no history entry (old
ratings arriving, not new ones). Run on import and after every scan, so a
film copied over later picks its rating up too.

**`tests/phone_serve.py`** (launch config `nextup-phone`, port 8776):
Next Up with `NEXTUP_PLATFORM=android`, sandboxed, with a library built the
way the phone's is — Akira, Aladdin, Dune, Parasite and Pantheon "found on
the phone" as empty stand-in files, fresh and unrated, plus the real PC
library imported as a snapshot. A pretend mpv prints what it was handed
and closes 3 s later as if 5 minutes were watched. Open at phone width.
It can't show Android itself: permissions, the media index, the real mpv,
the WebView.

## 2026-10-08 — v0.1.53 (cont.), play on the phone in the mpv app

"mpv is installed on the phone but nextup doesn't find it." It was never
looking for the app: on Android, play still ran the desktop lookup for an
mpv program, which the Play Store mpv isn't.

- On Android, `mpv_play` calls `android_play`, which calls the
  `ANDROID_PLAYER` hook set by `android/src/mobile/app.py`. `find_mpv`
  says plainly that channels and streams don't play on the phone yet, and
  Settings' mpv test says how the phone plays instead of looking for mpv.exe.
- `open_in_player` (app.py): the file's `content://` address from Android's
  media index (a file adb just pushed isn't indexed, so it's scanned and the
  answer waited for, 20 s max), an ACTION_VIEW lent read permission, aimed
  at `is.xyz.mpv`, with `position` in ms for RESUME. With no mpv, Android's
  "Play with" list instead.
- `note_now_playing` does nothing on Android: the player is another app
  with no line back, so nothing would ever see it end. Resume points and
  "watched" for phone plays are the next piece (mpv hands back position and
  duration as an activity result).
- Verified on the S24U: PLAY on Akira opened it in mpv.

## 2026-10-08 — v0.1.53, sizes in the copy tray

The user asked for sizes as you tick. The tray now lists every ticked film
or show with what it adds to the copy ("on drive" when it's there already,
"3.4 GB · 2 on drive" for a show partly there), and the count line carries
the total against the drive's free space, red when it won't fit.

- `/api/dock/plan` returns `items`: per poster key, `bytes` still to copy,
  `files`, and `already` on the drive.
- `trayQuote()` asks it 350 ms after the ticking stops (every source file
  is stat'd, and a sleeping drive can be slow), with a sequence guard so a
  late answer can't overwrite a newer one. Ticking, CLEAR, a drive change
  and a finished copy all re-ask.
- Ticking while CONFIRM — COPY x GB was showing now puts the button back
  to COPY TO DRIVE: the price it showed was for a different selection.

## 2026-10-08 — v0.1.52, one place to fill a drive: Library › Drives

The user's call: the docking station lives in Drives, and you fill a drive
by tapping tiles. The Settings docking card and the Library's SELECT were
the same job in two other places, and both are gone.

Drives has two views (**Show me**):

- **Your library — tap to add** (the default). Your library, only what's
  on this device, paged 120 at a time, marked against the drive picked.
  - A blue ✓ means on it, a red ✕ means not on it (dimmed), "3/10" means
    partly copied.
  - Tap a dimmed tile to tick it; one fully on the drive can't be ticked.
  - The tray underneath prices the copy (what's left, against free space,
    with a confirm), runs it and shows progress. Afterwards it re-reads the
    marks, so what was copied shows as on the drive.
- **What's on the drive:** the old read-only Drives view, unchanged.

It's the same machinery (`/api/dock/plan|start|status|present`), with the
tray and the marks now following Drives' own drive picker. Works the same
for USB drives and the phone. REREAD also re-lists the drives, so a phone
plugged in since the page opened turns up.

**One slip, caught in the browser:** reading the marks clears the tray's
status line, so the "Done — 2 of 2 copied" message vanished at once. The
marks are now read first and the message written after.

`tests/drives_serve.py` (launch config `nextup-drives`, port 8775) is the
sandbox with a pretend drive (a temp folder) and three small test films.
Its copy refuses anything else, because the sandbox's library points at
the real films on E:.

---

## 2026-10-08 — v0.1.51, the phone in the drive lists

The phone on the cable is now a drive like any other. It appears in the
docking station's picker and in Library › Drives as "Phone · James's S21
Ultra". Its ID is `phone:<serial>`; there's no letter.

- **Reading the phone:** one `find … -exec stat` over adb lists
  `Movies/Film & TV` with sizes, in `dock_drive_index`'s own shape, so the
  matching, the SELECT marks and the price all work unchanged. Read for
  real: all 7 films and 4 shows on the S21 matched, none unidentified.
- **Copying:** goes to `Film & TV/Films` and `Film & TV/TV` (the phone's
  folder says TV, not the drives' "TV Shows"). Each file is pushed under a
  `.nextup-part` name, its size is checked on the phone, then it's renamed.
  The push can't stop part way, so a cancel lands between files.
  Afterwards, if Next Up is open on the phone, it's asked to rescan, and
  the copies turn from grey to colour.
- **Quoting:** everything for the phone's shell is one string with each
  path quoted, the lesson of the `&` in "Film & TV". The test copies a film
  named with both `'` and `&`.
- **Test isolation:** `isolate()` still switches drive copying off.
  `phone_dock_test.py` keeps the real list and copy and points them only at
  a fake phone, a temp folder that its fake adb really reads and writes.
  Every real USB drive stays switched off.

---

## 2026-10-08 — v0.1.50, the phone on the cable, and a first phone layout

Asked for in one go on the S21, the test phone:

- **Film & TV.** The library folder is `Movies/Film & TV` (`Films/`,
  `TV/`), the user's own, which already held films. The old default is
  swapped over where it was the only folder.
- **Dark bars.** The status bar, navigation bar and launch screen use
  `#060509` with light icons. That's the pyproject colours, plus a run-time
  call for the navigation bar, which Briefcase's theme doesn't reach.
- **The phone on the cable** (Settings › Your phone › On the cable). The
  desktop app sees a phone plugged in with USB debugging allowed, by its
  own name, with its free space. **SEND MY LIBRARY** goes through an adb
  tunnel to the phone app's own server. It sets the TMDB key (the user
  chose this, so the phone can identify its own files and they match the
  catalogue rather than appearing twice), imports the catalogue (the phone
  fetches posters as it goes), then has the phone scan. It **never sends a
  video file**: the user's explicit condition, and tested.
  - Sent for real: 567 films, 78 shows, 2,409 episodes, 645 posters.
    Everything not on the phone shows greyed, "ON DESKTOP-O2K6QB8".
- **The Show list** is Show all / Part way through / Watchlist / On this
  device.
  - Not rated yet, Rated and Favourites are gone. The Favourites section
    is now the only way to favourites, and the list narrows it: shelves
    combine, as in `favourite+here`.
  - "Not on this device" was tried and dropped, at the user's word: nobody
    wants to see only what isn't there.
- **A stale-grid bug, old.** Two Library loads in flight could draw in
  either order, so switching Favourites → Films quickly showed favourites
  under FILMS, 4 times out of 4. Loads are now numbered, and only the
  latest draws.
- **The phone layout, first pass.** A `max-width:600px` block at the end of
  the main stylesheet; the desktop window never goes under 760, so it's
  phone-only.
  - The main tabs move above the Library's rows.
  - A film or show page goes to one column. It had been the desktop grid,
    which left the text a 73 px strip, one word per line. Now the text is
    317 px wide, with cast and similar stacked underneath.
  - The desktop is unchanged, measured: 180 + 662 px columns, side panels
    451 + 451.

Also in this batch:

- **A clean-up mistake.** `check_storage.py`'s clean-up never ran, twice:
  `adb shell` joins its arguments for the phone's shell, which read the `&`
  in "Film & TV" as "background" and the brackets as syntax. It left two
  51 MB dummies on the phone, now removed, and the paths are now quoted.
- **mpv on the phone stays a separate install.** It's the mpv app, handed
  each film by intent in step 5. Building libmpv in is possible, but
  that's native builds, ~50 MB, and our own player controls.

---

## 2026-10-08 — v0.1.49, Next Up runs on Android (the shell)

Step 3 of the Android plan (`docs/superpowers/plans/2026-10-08-android-
shell.md`). On the test phone (Galaxy S21 Ultra, Android 15), the APK starts
Next Up's own server inside the app and shows the page full-screen. All five
tabs and every Library section open with no page errors, and the app sees
films in `Movies/Next Up/`.

**`nextup.py` learned three things, none of which changes the desktop:**

- **`DATA`**, where everything it writes lives. It's `NEXTUP_HOME` if set,
  otherwise `HERE` as before. The app points it at its private data folder
  before importing, because Android replaces the code folder on every
  update and a library kept beside it would go too.
- **`PLATFORM`**, which is `"android"` there (Python reports
  `sys.platform == "android"`).
- **`serve_in_thread()`:** the start-up `main()` did inline. It tries the
  following ports if one is taken, because a phone that killed and
  restarted the app may still hold the last one. The desktop asks for
  exactly one.

**The app** (`android/`, id `app.nextup.mobile`; "mobile" because a package
named `nextup` collides with `nextup.py`) is a Toga `WebView` on
`127.0.0.1`. A failed start-up shows the traceback on screen rather than a
white page.

- `build.py` copies `nextup.py` and its assets in, then builds and
  installs. Briefcase only writes the manifest when it *creates* the
  project, so a changed `pyproject.toml` now recreates it. Without that,
  the new video permission silently never reached the phone.
- `check_device.py` launches the app and reads the log.
- `check_page.py` attaches Chrome's debugging protocol to the WebView over
  adb, clicks through everything, and fails on any page error. The WebView
  sends nothing to logcat, so a quiet log proved nothing. `--selftest`
  throws one on purpose to prove the check can fail.
- `check_storage.py` pushes a 51 MB dummy film and asks the app's own scan
  to find it.

**Unknowns settled:**

- **Python 3.14 builds fine** (Chaquopy).
- **The page works in the WebView unchanged**, at 384 px wide.
- **`READ_MEDIA_VIDEO` plus plain file paths reads `Movies/Next Up/`** on
  One UI / Android 15. The user tapped Allow on Android's own prompt. No
  fallback folder needed.

**Seen on a fresh install, for the polish step:** the profile is named
after Android's user ("U0_a429") and the device "localhost".

---

## 2026-10-07 — v0.1.48, the phone link (PC side)

The user got a Galaxy S24 Ultra and wants Next Up on it the way the Mac
has it: a separate app with its own library, stored on the phone (1 TB),
populated by this one. Design: `docs/superpowers/specs/2026-10-07-android-
app-design.md`. Plan for this step: `docs/superpowers/plans/2026-10-07-
phone-link-pc-side.md`. The cloud-folder sharing the Mac uses can't reach a
phone, because OneDrive on Android keeps no real folder. So the phone talks
to this PC directly, over home Wi-Fi. This version is that PC side. The app
itself comes next.

**What's there.** A second server on port 8790, off until "Let a phone
connect" is ticked in Settings → Your phone. It's served by `PhoneHandler`,
a class with *only* the phone's routes. The allow-list holds by
construction: the bin, settings, the sorter, mpv and scans aren't refused
there, they don't exist. Requests from outside the private address ranges
get 403, so a forwarded router port wouldn't put a 4-digit code on the
internet.

- **Pairing:** PAIR A PHONE shows a code for 5 minutes, which dies after
  5 wrong tries. It's swapped for a `secrets.token_urlsafe(32)` token, and
  only the token's SHA-256 is kept in the config.
- **`/phone/snapshot`:** the library snapshot with a file key on everything
  (`m<tmdb>`, `e<tmdb>s<n>e<n>`). It has no sizes: stat-ing ~3,000 files on
  E: is the stall the app learned to fear, and the download states its own
  size. No path ever comes from the phone.
- **`/phone/file`:** ranged, so a dropped download resumes. A bad range
  gets 416 with `bytes */size`. A drive that doesn't answer within the 3 s
  check gets 503 ("try again"), not 404: asleep isn't gone.
- **`/phone/sync`:**
  - GET is this PC's history, the seeds, and every *other* device's events
    from the inbox, so the Mac reaches the phone through here.
  - POST is the phone's whole file, keeping only lines in the phone's own
    name.
  - With cloud sharing on, it's saved straight into the shared folder and
    the Mac reads it there, with the PC as courier. With it off, it goes in
    `nextup_phone_sync/` and is taken in on the spot.
  - It never touches `history.shared`, which belongs to the cloud folder.
- **Discovery:** the same port number answers `NEXTUP?` over UDP, so the
  phone needs no IP address typed in.

**The final review** (a fresh reviewer over the whole branch) found five
things worth fixing before shipping, each now with a test that failed
first:

- **Downloads of files named outside Latin-1 broke.** A name like "Don’t
  Look Up – 2021.mkv" raised while sending headers, after a 200 had
  already promised a film, so the phone received an error message as the
  film's opening bytes. The name now goes RFC 5987 style
  (`filename*=UTF-8''…`).
- **A phone could pair under the Mac's id or this PC's.** In cloud mode its
  upload would then *replace* that device's history file. Ids already in
  use are refused. A phone paired before (`known_ids`, kept after FORGET)
  can always come back.
- **`except OSError: pass` hid real failures.** OneDrive holding the file
  meant a silently dropped connection. Now only a hang-up is quiet.
  Anything else is logged and answered: 503 for an OSError, 500 otherwise,
  or the connection is closed if a reply had already begun.
- **The sync body isn't append-only, but sync_import resumes by offset.**
  On the PC side the phone's file is now read from the top every time. The
  phone side must do the same with the PC's; that rule is written into the
  spec.
- **Turning the link off didn't end connections already open.**
  `server.shutdown()` only stops new ones, so a kept-alive connection went
  on serving, a film download included. Open connections are tracked and
  shut on stop, and on FORGET for that phone.

The sandbox (`isolate`) forces the link off and, if a test turns it on,
binds 127.0.0.1:8791 only. Every interface would raise a Windows Firewall
prompt on the user's desktop. Test: `phone_link_test.py` (43 checks).

---

## 2026-10-03 — v0.1.47, Cold Ones #22, a channel from YouTube

The user wanted Cold Ones on Next Up as a channel of their own, random
videos on a loop. It's a new channel `type`, `youtube`, with a `source`
(the creator's uploads page), and the schedule is exactly the other
channels': a fixed list, sorted by id, shuffled by the channel's seed,
looping from 2024. Only where the list comes from is new.

`yt-dlp --flat-playlist -J` reads the whole uploads page in one request
(173 videos, about 3 seconds, every one with its length). It is never run
while a page waits. The Channels page builds every schedule on each load,
so the list is read from `nextup_youtube.json`, and a stale or missing one
is refreshed on its own thread: daily, with a ten-minute back-off after a
failure, keeping the old list when a refresh fails. Shorts (under 2 min),
premieres and live streams are left out. A " | Cold Ones" signature on a
title is trimmed off, since the card already says Cold Ones.

A block of kind `youtube` plays through `mpv_play` with the page address
and `keep_open`, so it holds the window and hands on at the end like any
channel. `_block_identity`, `channel_play_target` and `_play_display` each
learned the kind. History gets the tune-ins. There's no watch record yet,
since these aren't library items.

**One trap, found in the first real run:** YouTube refused the stream (403)
to the installed yt-dlp, which is 90+ days old. mpv goes straight to idle,
which reads exactly like "the video ended", so the channel would have
handed on to the next video, been refused, handed on again, and raced
through all 173. A YouTube video that "ends" with no position past 5s now
stops the channel, closes the window, and the card says yt-dlp needs
updating until one plays. **The channel won't actually play until yt-dlp
is upgraded.** That's parked in PLANNED.md.

Test: `youtube_test.py` (25 checks, fake yt-dlp, mpv stubbed). The sandbox
redirects `YOUTUBE_PATH`, and `run_all` guards it.

---

## 2026-10-03 — v0.1.46, one line after all

Seen in use, the second row cost ~50px of every Library screen for three
buttons, and the user asked for it back up on the shelves' line, keeping the
new look and keeping it clearly a separate tier. `#libplaces` now lives in
the masthead after `#libnav`, behind a hairline `--line` divider, and hides
off the Library the same way the shelves do (`visibility`, so the main tabs
never jump).

Shelves, places and main tabs come to ~980px with every word in. Measured by
narrowing the header in 4px steps: the line broke at 901-915px. Below a
940px header (about a 990px window) the places drop their words and keep the
icons, with the name in the tooltip and aria-label. The shelves keep their
words because they're what you reach for most. After that, no width from
1072 down to the 760px window minimum breaks the line.

---

## 2026-10-03 — v0.1.45, two rows for the Library

The user found FILMS-to-DRIVES too cluttered: six sections on one line, read
as one list of equals, when they're two kinds of thing. FILMS, TV SHOWS and
FAVOURITES are your shelf, browsed the same way. HISTORY, RECOMMENDATIONS
and DRIVES are places you go from it. Their ask: the shelves alone up top,
the other three in a row of their own that's clearly separate and doesn't
move as you flick between sections. YouTube, when it comes, joins the
shelves beside Favourites.

`LIB_SECTIONS` is now `LIB_SHELVES` and `LIB_PLACES`, both drawn by the one
`drawLibNav()` with the same click handler, so nothing about how a section
opens changed. The shelves stay in the masthead. The places are a
`#libplaces` row, the first thing inside `#view-library`. That puts it in the
same spot on all six sections (measured: same top on every one), and it
leaves with the view instead of leaving a blank strip on Now and Rate. It is
styled to read as a different kind of row: sentence case in the body face,
an icon each, and a soft filled pill for the one you're on, with the
marigold kept for the icon rather than an underline.

One trap, caught in the screenshot: `#view-library` clips its overflow, and
the first version pulled the row up 8px and left 10px to tighten it against
the masthead and line the icons up with FILMS. That sliced the top and left
edges off the selected pill. No negative margins now. The icons sit a
pill's padding in from FILMS, which is the price of the pill.

Checked at full width and at the 760px minimum: the shelves still share the
masthead line, all three places fit one line, nothing scrolls sideways, and
a sort set on Films survives a trip to History and back.

---

## 2026-10-02 — v0.1.44, loose downloads, and the blank TV tiles

### The sorter only ever looked at folders

Asked whether the built-in sorter only looks at folders: it did, twice over.
The user's `process_new_movies.py` took its items from the Torrents root with
`p.is_dir()`, and the app's own "waiting" list did the same, so a torrent
that arrived as a single file — two South Park episodes and a film, that
morning — was neither sorted nor shown. Nothing said so.

The script (backed up first; it isn't under git) now treats a loose
`.mkv`/`.mp4`/`.avi` in the root as an item. The dry run reports it like any
other. The real run gives it a folder of its own named for the file,
carries along any subtitle that starts with the same name, and then hands
that folder to the existing path unchanged. That was the smaller change by
far: every step after the check (junk stripping, extras, duplicates, the
spreadsheet) assumes a folder, and wrapping the file once is cheaper and
safer than teaching each step about files. Samples on their own aren't items.
The five-minute "still being written" rule applies to a loose file by its
own modified time. `sorter_waiting()` lists loose videos too, using the
script's three extensions rather than the app's longer `VIDEO_EXT`, so it
never shows a `.mov` as waiting for a script that won't touch it. The
routine's rulebook (`process-new-movies.md`) used to tell it to ignore loose
files; it now says a loose video is a new item.

`sorter_test.py` adds a loose film with its subtitle and a loose episode of a
show arriving in the same run as its season folder (20 checks). The real
folder's dry run then routed both South Park episodes to the existing show.

### Blank TV tiles

Seven shows in the TV grid had nothing in them: six with no poster, titled
like the release folders they came from ("Futurama S05", "South Park Season
13 S13 + Extras", "Rick and Morty S04 -KONTRAST"), and BoJack Horseman, which
had a poster but no files left on the drive. Every one had zero episodes. The
scan deletes the row of a file that has gone, but a show row was never
deleted. So when the sorter merged a release folder into the real show, the
episodes moved across and the old show stayed behind as a blank tile.

The scan now drops a show with no episodes, in the same step as the files
and behind the same guard against an unplugged drive. Anything you've put
on it keeps it: a score, the watchlist, a favourite, or watch time, because
that's yours and the files may come back. A rescan of a copy of the real
library removed exactly those seven and changed no episode or film. They go
from the live app on its next library scan. Test: `empty_shows_test.py`
(5 checks).

---

## 2026-09-28 — v0.1.43, the first design pass, on Settings

The first job for the new `ui-designer` agent (`.claude/agents/`). It wasn't
loaded yet in the session that wrote it, so a general agent was told to read
the file and follow it — which made the run a test of the instructions as
much as of the page.

### What it fixed

Eleven things, all styling, markup and wording, no behaviour, gathered in one
commented `-- settings` block at the end of THE FACELIFT:

- **The docking station's selection count was invisible below 1340px** — the
  row borrowed the Library toolbar's `.searchrow`, and with it that toolbar's
  rule hiding the count on narrower windows. Here the count is the only place
  a selection spanning pages is totalled.
- Four card headings sat 22px lower than the other three (leftover inline
  margins); all seven now measure the same.
- Save buttons were "Save", "Save settings", "Save", "Save subtitle
  settings", in sentence case where every other primary button is caps, and
  "Save settings" saved only the TMDB key. Now SAVE, SAVE KEY, SAVE, SAVE, all
  in the same button row.
- The four-field rows (still watching?, subtitles) broke three-and-an-orphan
  at 760px and with the queue docked. Each card is now a size container: four
  across from 700px of card, two by two below — keyed on the card, not the
  window, the same rule as the Rate card.
- Rows in "What's stored" were indented 34px by an empty rank column borrowed
  from the numbered lists; the checkbox was system blue, the only blue in the
  app; `<code>` fell back to the browser's monospace; explanations ran about
  140 characters a line (now capped near 80); the duplicate-copies details
  touched its buttons; the folders box could be dragged out of its card.
- Wording: "1 of your old copy", "3 things… if a scan brings it in".

Checked independently afterwards rather than taken on the report: the diff
read line by line, headings, grid columns and the count measured at 760 and
1000, all 162 checks passing, and the real config, library, downloads folder
and OneDrive sharing folder untouched.

Six bigger findings came back as proposals, the most important being that
saving one card silently discards unsaved edits in the others. They're in
PLANNED.md.

### What it found about the sandbox

The instructions said clicking anything in the dev server was safe. It
wasn't: `isolate()` sandboxed the app's own files, but SHARE THROUGH ONEDRIVE
would have written test history into the real sharing folder, the docking
station copies to real USB drives, the sorter acts on the real downloads
folder — and MOVE TO BIN in the duplicates review would have binned real
films, because the sandbox's library is a copy whose paths point at the real
media. The agent noticed and kept clear. Those routes are now switched off
inside `isolate()` itself (a test that needs one puts a stand-in back), so
nobody has to remember. mpv and SCAN MY FOLDERS still reach the real thing,
and the instructions now say so.

Its other notes on its own instructions were folded back in: how to pass the
profile picker from script, rendering a state with made-up data instead of
causing it, treating screenshots as rough, where the page-parse check lives,
and the borrowed-class trap as a layout rule.

---

## 2026-09-27 — the tests move in

Every test suite written since August lived in a Claude session's scratch
folder under `AppData\Local\Temp` — a folder Windows may clear whenever it
likes, and one no later session would know to look in. They now live in
`tests\` here: seven suites, 162 checks, run together with
`python tests\run_all.py` in about a minute, plus the sandboxed dev servers
and the pick audits. `tests\README.md` says what each proves.

Two things changed on the way. Scratch output (fake download folders, the
sync test's two pretend computers) goes to `tests\_work` rather than beside
the scripts — and that folder holds copies of the real library and config,
passwords included, so it must never be shared. And `recs_test.py` was left
behind: it was a probe that wrote to the real TMDB cache, which breaks the
one rule the folder has.

No change to the app itself, so no new version.

### And a history

The same day, the folder became a git repository — local only, nothing
uploaded. Every change from here is a snapshot with a note, so any past
version can be looked at, compared or undone, and the question "when did
Favourites break?" (answer: v0.1.20, found by hand nine versions later) has
a lookup instead of an investigation. The whole history of `nextup.py` will
cost megabytes where `Old versions and extras` costs 1.5GB.

`.gitignore` keeps out everything private or rebuildable — the config with
its keys and password, the library with its watch history, `tests\_work`,
the TMDB cache, the artwork, the built `.exe`, and the old versions — and
the staged files were searched for the config's actual secrets before the
first commit: none present. A copy on GitHub, which is what would bring the
Mac up to date in one step, is in PLANNED.md.

---

## 2026-09-25 — v0.1.42, the Watch Score

Asked for: a hidden number on every title — one for a film, one for a whole
show — that corresponds to watch time and moves relative to the others. To
be used later; nothing shows it yet. Shaped over four messages: count only
from when the sleep timer existed, 0 to 99, and films scored against films,
shows against shows.

Two new columns on `movies` and `shows`. `watch_seconds` is the absolute
measure: every watched or stopped sitting in the history, each counted as
the time the player was open, capped at the title's own length — a paused
film left on overnight is not twelve hours of it. The older finished rows
that carry no timing count the full length. `watch_score` is a whole number
0–99: your most-watched film is 99 among films and your most-watched show
99 among shows, everything else placed against those on a log scale (a
sitcom on most nights runs to dozens of hours; on a straight line every
one-off would sit at 2 or 3). Any watch time at all scores at least 1, so 0
means exactly never watched, and never-watched titles hold 0 rather than
NULL.

**Counting starts at 2026-09-22 23:58:07**, the first start of a version
with the "are you still watching?" timer, read from nextup_errors.log —
before that one night asleep could run a season into the score. That
leaves 18 sittings to go on and 329 older ones out, so today only four
shows have a score (My Hero Academia 99, Seinfeld 53, Band of Brothers 48,
Sunny 1) and no film does yet. The earlier history is untouched; it just
doesn't count here.

It is recomputed after every sitting, after another machine's sittings
arrive by sync (on the sync's own connection — a second one would wait out
the lock), and once at startup: 47ms for the whole library. Derived, so
never synced itself; each machine works it out from the history it holds.
`/api/watch-scores` lists the table for looking at and is linked from
nowhere.

Suites: queue 19, sleep timer 61, port 10, sync 27.

---

## 2026-09-25 — v0.1.41, missing episodes that you already have

Reported as: the missing-episodes section of Recommendations doesn't
update.

It couldn't. A recommendations scan asks TMDB how long every season is and
saves the result, and the page showed that saved result until the next
scan — so episodes you'd since added stayed listed as missing. The saved
scan was from 17 September; Futurama said 91 missing a week after seasons
6 to 8 and S02E20 arrived.

The season lengths are what the scan is for, and they keep. What you own
is the library's to answer, and it changes. `fresh_gaps` now re-checks the
saved list against the library every time the page asks — no TMDB, one
pass over the episodes — and drops any show with nothing left missing. The
saved scan itself is never rewritten. Against the real saved result:
Futurama 91 → 28 (seasons 9–11, which genuinely aren't there), South Park
118 → 104.

What it can't do is find a gap that opened after the scan — a new season
aired, say. That still needs a scan, because only TMDB knows.

It looked at first as though Futurama's two season numberings (broadcast on
TMDB, DVD in the files) might be making phantom gaps. They aren't: a season
where you own more than TMDB lists simply reads as complete.

---

## 2026-09-25 — v0.1.40, the episode you watched last, and any episode of a favourite

Asked for: shows like Seinfeld and It's Always Sunny, which have been seen
end to end, should be suggested as random episodes; "continue where you
left off" should follow the episode most recently watched, not the one
furthest along; and pressing play should still go on in order. The app
can't know a show has been seen in full — it only saw the plays it was
there for — so, as suggested, favouriting is the signal.

### Where you are is where you were last

`series_progress` answered "where am I in this show" with the episode
furthest along the run: any half-watched episode at all beat a finished
one, and among them the latest in the series won. Right for a show watched
in order, wrong for every other kind. Sunny had thirteen half-finished
episodes from S01 to S16, so the answer was one of those rather than the
S17E01 just watched; Seinfeld said S09E16 on the night S06E20–21 were
on. Fifteen of 86 shows gave a different answer.

It is now the most recently played episode: stopped part way means resume
it, finished means the one after it. A position of a few seconds on an
episode already finished doesn't count as stopping part way — that's a
rewatch opened and closed. With no timestamps to go on the furthest still
wins, which is the old reading. The Library's continue tile, the Now tab,
queueing a show and PLAY on a show all ask this one function, so they all
agree. The tile now also shows the next episode after one you finished
("up next"), dated by when you watched the one before it — otherwise
finishing S17E01 left it showing something half-watched from months ago.

### A favourite is any episode

On the Now tab a favourite show's episode is drawn at random, avoiding
anything played in the last 45 days while there's something else. Once it
plays, the next episode in order follows — that part never changed, the
run follows from wherever it starts.

The bonus a favourite gets was measured, not guessed: v0.1.39's logic
rebuilt alongside and each drawn 4,500 times against a copy of the real
library. At 1.5 favourites fell from 8.6% of TV suggestions to 7.7%; at
2.0 — the "part way through" bonus most of them used to earn — they sit at
10.7%, each show at or above where it was. `FAVOURITE_BONUS` is 2.0.

### Two shows that had quietly vanished

The measuring turned up that **Seinfeld had been offered 0 times in 4,500
draws** under the old logic. Its "current" episode was an old half-watched
one that had also been seen to the end within the month, and the Now tab's
rule against offering anything watched in the last 30 days hid the whole
show. The new anchoring briefly did the same to My Hero Academia: S01E05
is where you are, and it was also played through on the night of the
autoplay. An episode you're part way through is now exempt from that rule —
picking it back up is the point — though anything turned down this session
still counts. Seven shows came back into the draw.

---

## 2026-09-24 — v0.1.39, the better copy wins, and nothing is deleted without asking

Reported as: accidentally downloaded all of Futurama 1–7 while owning most
of it — what happened to the files already there?

### What had happened

Nothing was replaced. The sorter's rule for an episode it already had was
to skip it — and then `shutil.rmtree` the whole download folder, skipped
copies included, straight past the Recycle Bin. Checked three ways rather
than one: every file in Seasons 1–6 still had its original creation date
(July to mid-September), the library's `added` column put every Season 7
episode at 12:33 that day (so there was no older Season 7 to lose), and
nothing the library knew about was missing from disk. New: all 26 of
Season 7 and S02E20, which filled a gap. About a hundred duplicate episodes
were deleted outright.

That cost nothing this time — ffprobe showed the release's early seasons
were 706×480 against the library's 1440×1080 — but only by luck. Had the
download been the upgrade, the upgrade is what would have been destroyed,
and the only trace would have been a line in the report. Films had the
same flaw: "REFUSED to overwrite", then the same `rmtree`.

### The rule now

The change is in the user's own `process_new_movies.py` (backed up first
as `process_new_movies.py.before-duplicates-2026-09-24`), because that's
where the rule lives and where the scheduled task runs it too.

- **The better copy wins.** Resolution first, judged by whichever of width
  and height says more, so 4:3 at 1440×1080 and scope at 1920×800 both read
  as 1080p. Bitrate only breaks a tie within the same codec and by more
  than 25% — bitrates across codecs aren't comparable, and every swap
  leaves a file behind. Anything that can't be measured keeps yours.
- **An upgrade takes your filename.** It carries the episode title and it
  is the path the library knows. When the extension changes (.mp4 → .mkv)
  the path changes anyway, and a scan would have read that as one film gone
  and another arrived — rating lost. So the script logs `replaced`/`by`, and
  Next Up moves the library row to the new path before any scan, including
  scans after a sort it didn't run itself.
- **The loser is moved, not deleted,** into `_DUPLICATES/<release>/`, with a
  line in `_DUPLICATES/PENDING.jsonl` saying what it is, why it lost and
  which copy was kept.
- **Films check the folder, not one filename.** `Heat.mp4` is already Heat
  when the download is `Heat.mkv`; before, both would have landed side by
  side. And a film you already had is no longer added to the spreadsheet a
  second time.
- **The dry run says it first:** "YOU ALREADY HAVE 3 OF 4 EPISODES — the
  better copy of each is kept, the other set aside".

### The asking

Settings, under the sort button: *N duplicate copies set aside · size*,
what each one is and why it lost, and MOVE TO BIN / SHOW FOLDER / NOT NOW.
Binning uses the same `send_to_trash` as the duplicates review — the
Recycle Bin, never an unlink — then rewrites the log and removes only
release folders that emptying left empty. It shows whenever anything is
waiting, so a sort the scheduled task ran without the app still gets asked
about. The task's rulebook, `E:\Torrents\process-new-movies.md`, was brought
into line (backed up alongside): it used to tell the task to replace
episodes by hand, and it now says duplicates are the script's job and
`_DUPLICATES` is not to be touched.

### Checked

24 checks against a fake downloads folder of real two-second videos at
480p, 720p and 1080p, run through the app's own sorter code with the
Recycle Bin swapped for a scratch folder: 11 videos before and 11 after,
each case landing the right way, the rating following a film from .mp4 to
.mkv, and the real `E:\Torrents` fingerprinted unchanged. Then the real
script was dry-run in place — nothing waiting, its state file restored
byte for byte.

---

## 2026-09-23 — v0.1.38, the Rate card grows up

Four asks in one sitting, all for the card on the Rate tab.

### The picture behind it

The Now tab's backdrop, drawn the same way — `heroNode`, the same mask
and opacity — and loaded the same way: while you look at one card, the
next one's backdrop and poster are fetched, so rating or skipping never
shows a card with its picture still arriving. Checked across three
ratings in a row: the next card's art was already in the cache every time.
241 of 242 unrated films and 40 of 46 shows have a backdrop.

### A card was being skipped on every rating

Found while checking the look-ahead, and not asked for. Rating a card
takes it out of the unrated list, so the next card slides into the same
position by itself — and the code then stepped forward one as well. Every
rating silently jumped a card, which only came back when the queue wrapped
round. Proven before the fix (rating *Warfare* went straight past *Dogma*
to *Star Trek II*) and after it (three ratings, each landing on the
expected card). SKIP still steps; rating no longer does.

### One size of card

The card changed height with every film, so the rating notches and the
buttons moved up and down the screen as you worked through the queue. It
is now one height, taken from measurement rather than a guess: every one
of the 242 films and 46 shows was drawn and its natural height taken. The
longest needs 534px on a card 960px wide and 573px at 740px, so the card
is 540px, or 590px when the card itself is narrower than 900px. That is a
container query on the card's own width rather than a media query on the
window's, because the docked queue panel takes 300px off it too. Result: all
288 cards the same height at both widths, and the buttons in exactly one
position. The spare space sits above the buttons, which are pinned to the
foot.

The first attempt stretched the poster to the card's full height, and
`object-fit` cropped it to a sliver of the middle — *Heat* read "E A". The
poster now keeps its own shape at the top.

### The whole description, and the studio's line

The description was cut at 200 characters with an ellipsis; 374 of the
558 films have longer ones, up to 728 characters. It's sent whole now.

The tagline tile is TMDB's own `tagline` field — the poster line, "A Los
Angeles crime saga." — which was already in the database for 539 of 558
films and only ever read by the detail page. Shows have none stored, so
their cards don't draw the tile.

What was actually asked for was a different kind of line — "DiCaprio stars
in a film about Wall Street" — which TMDB doesn't have. Built from its
keywords it goes wrong too often to trust: *Wolf of Wall Street* lists
"corruption" first and "wall street" seventh, *Babylon* leads with
"elephant". Written properly it needs a language model, which is a
decision about keys and cost rather than a thing to do in passing — noted
in PLANNED.md.

---

## 2026-09-23 — v0.1.37, the Rate tab stops showing TMDB's number

Asked for: take the TMDB score off the Rate tab.

It is the right call for a reason beyond tidiness. The Rate tab is where
your own score gets made, and a public average printed just above the
ten notches is an anchor — the easiest thing in the world is to land a
point either side of it. Your ratings are what the recommendations and
the picking learn from, so a rating nudged towards TMDB's teaches them
TMDB's taste instead of yours.

Gone from both places on the tab: under the thing being rated, and beside
each title in the top-rated lists, which now show just the year. The score
is still on each film's own page, and still feeds the picking at its
reduced weight.

---

## 2026-09-23 — v0.1.36, Favourites was showing everything

Reported as: pressing Favourites just shows the Films tab. It did, near
enough — all 558 films.

The cause was in `browse_library`, in the chain of shelf filters. Hiding
the greyed-out titles from another machine on the Part way through,
Watchlist and Favourites shelves had been written as an `if` in the
*middle* of the `elif` chain, so the watchlist and favourites branches
after it could never run. Both shelves quietly showed the whole library.
It arrived with the Mac work in v0.1.20 and went unnoticed for nine
versions, because a full shelf looks like a working one until you count
it. The filters come first now and the elsewhere step runs after them, on
its own.

A second, smaller fault sat on top of it: the Favourites tab asked for
films only, while choosing Favourites from the Shelf dropdown asked for
films and shows. The tab asks for both now, since that is what a
favourites shelf is.

Checked against the library itself, not against the page: 27 favourites
(22 films, 5 shows) and 28 on the watchlist, matching the counts of
flagged rows exactly.

---

## 2026-09-23 — v0.1.35, the resume tile follows the shelf

Asked for: the "continue where you left off" tile should show the last
film on Films and the last show on TV shows.

It showed the single most recent thing, whichever kind it was, on both —
on the day this was asked, The 40 Year Old Virgin sat on the TV shelf
ahead of My Hero Academia. The page now picks by shelf: the newest film on
Films, the newest show on TV shows, and simply the newest on Favourites,
which holds both. Switching shelf repaints it from what is already loaded;
there is no second fetch.

The server had to change too. It sent only the four most recent items, so
four films in a row would have left the TV shelf with nothing to show even
with a show half watched. `/api/resume` now sends the whole in-progress
list, which is short by nature. A shelf with nothing of its own part way
through shows no tile rather than borrowing one from the other kind.

---

## 2026-09-22 — v0.1.34, ninety minutes after midnight

The after-midnight default was forty-five minutes, chosen against the
night that prompted the timer: 24-minute episodes, so it would have asked
after the second one. It was never checked against anything longer. A
45-minute drama exceeds forty-five minutes on its own, so after midnight
the question would have come up at *every* episode — the kind of nagging
that gets a timer switched off, which is worse than no timer.

Ninety now: two episodes of nearly anything, three or four of anime. A
season still can't run out, and a late film or a pair of episodes goes
uninterrupted. The rule of thumb for picking these numbers: the question
arrives roughly every *band ÷ episode length* episodes when nobody touches
anything, so a band shorter than a long episode means every episode.

Only the default moved. A value already saved in Settings is left alone.

---

## 2026-09-22 — v0.1.33, "are you still watching?"

Reported as: fell asleep during episode 1 of My Hero Academia, and the whole
season played out. The PC didn't sleep either — mpv holds the machine awake
for as long as it is playing, so the room kept the lights on until the show
ran out of episodes.

Three things in this app carry on by themselves: an episode run, the queue,
and a channel. That is the point of all three, and it is also the failure.

### It asks between programmes, never over one

A question over the middle of a film would be a worse interruption than the
thing it is protecting you from. A hand-over is the one moment where
stopping costs nothing, and `_finish_current` was already the single funnel
every hand-over goes through — the channel, the queue and the next episode
all leave by the same door. The dispatch came out of it into `_hand_over`,
which the timer can hold and run later, unchanged, if you say you are there.

It is only asked when something actually would have followed. "Are you still
watching?" over a player that was about to close anyway is a question with
nothing riding on it, so `_would_follow` checks first — including whether the
show has another episode at all.

### The clock at the moment of the question

The setting had to move with the time of day: one number is either too
nagging at four in the afternoon or too forgiving at two in the morning, and
the second one is how you end up switching it off. Three bands, adjustable
in Settings, defaulting to four hours in the daytime, two and a half in the
evening, **forty-five minutes after midnight**.

The band is read **when the question is asked, not when playback started**.
A film put on at half eleven ends at two, and two in the morning is the
number that matters. Getting that backwards would make the timer useless on
exactly the nights it is for. A band set to 0 means never ask then, which is
the one way to have it off in the daytime only.

### Knowing whether anybody is there

Two signals, because either alone is wrong.

Every POST to the server is somebody doing something — nothing in the app
polls with one, only with GETs — so `seen_you()` sits at the top of
`do_POST` and covers every button in the page and on the remote.

That is not enough on its own: an hour of watching a film is an hour of
touching nothing here. The other half is mpv's own keyboard, read from the
monitor's existing once-a-second tick. Pausing is a person. A jump forward
is a person. A jump *backward* had to be handled more carefully — a drive
that stops answering for a few seconds looks exactly like a rewind from the
outside, and E: does that. So a forward gap between the position and the
wall clock counts, and a backward one only counts when the position itself
moves backwards, which no stall can do.

**The bug that would have made the whole thing never fire:** at a hand-over
the position drops from the end of one file to the start of the next, and
that is a rewind to anything watching positions. Every single episode change
would have marked you present. `afk_new_file` resets the tracker whenever
something starts, and a test now replays that exact pair of ticks.

### Asking in three places at once

There is no telling which window is in front of you, so: mpv comes out of
fullscreen — the app is usually directly behind it — the question goes on
mpv's own on-screen display for whoever is looking at that, and the app
raises its own window and draws it properly. Raising happens on a thread of
its own; nothing about asking a question is worth risking the one thread
that watches playback.

The card is not dismissable. No close cross, and Escape does nothing — the
two buttons are the ways out. So is ignoring it: after five minutes with no
answer the player is closed, which is the half of this that lets the machine
get to sleep afterwards, and the reason the question isn't simply left up
all night.

Nothing is marked as watched that wasn't. The hand-over is held *before* it
happens, so the queue still holds its items and the episode you slept
through was never started.

Sixty-one checks, against an isolated copy of everything the app writes.
The queue's own nineteen still pass, which was the point of keeping the
hand-over dispatch byte-for-byte what it was.

What it deliberately doesn't do yet is written down in PLANNED.md: the
remote doesn't show the question, a single very long film is never
interrupted, and the mouse doesn't count as being there.

---

## 2026-09-20 — v0.1.32, a week of history, and a tab that takes you home

### PLANNED.md

The open items moved out of the top of this file into one of their own,
ordered by how much they matter rather than by when they were thought of:
the Mac update pinned at the top as the standing job, the phone and the
archive prune below as wanted-but-not-urgent, the X-Men '97 merge as a
decision, the launcher essay as an idea. This file goes back to being only
the record of what has been done.

The reason is worth stating: a conversation gets summarised away when it
grows too long, and four of those items existed nowhere but in one. A file
does not have that problem.

### History opens on a week

Reported as: the page has grown too long to read. It had — 302 rows, which
is every evening since the app existed, and the question it usually answers
is "what did I watch this week". Forty-one rows now, and the end of the
list says how far back you are looking and offers the next step: a week, a
month, three months, a year, everything. The "Going back" select still sits
at the top for anyone who knows the answer they want.

The empty case matters more than the full one: nothing watched in the last
week is precisely when the way further back has to be there, so the same
control is drawn under the empty message.

Wording caught by reading it rather than by testing it: the label list was
written for the button ("GO BACK A MONTH") and reused in the sentence,
which produced "That's the last a week." Two forms now, one for each place.

### The tab you're on takes you home

Asked for: pressing LIBRARY while in History should go back to the shelf.

It should, and the Library is the case that needed it — its sections live
*inside* it, so after a while in History or Drives the only way back to the
posters was to find the right sub-tab. Pressing the tab you are already on
now resets that tab: Films, first page, nothing searched, no shelf filter,
A to Z, and selection mode off if it was on.

The other tabs get the same gesture with the meaning they each deserve.
Channels and Rate reload; everything scrolls back to the top. **The Now tab
deliberately keeps its pick** — throwing away a suggestion because someone
pressed the tab would be a strange way to reward the press.

---

## 2026-09-20 — v0.1.31, a button for the sorting

Asked for: the thing a scheduled assistant does every night — sort new
downloads into MOVIES and TV — as a button in Settings, beside SCAN MY
FOLDERS, with a dry run first every time and a downloads folder that can be
set rather than assumed.

**Nothing here sorts anything.** `process_new_movies.py` already does that,
it lives in the downloads folder, and it is the thing that knows this
library's conventions — flat shows versus season folders, which junk to
strip, where extras go, how the spreadsheet is striped. Reimplementing it
would have meant two subtly different sorters and a library that slowly
disagrees with itself. So the app runs it, shows what it intends to do
first, and finishes the one job the script's own docstring says it cannot:

> NOT automated here (needs live web lookup): fetching missing TV episode
> titles from Wikipedia.

That lookup is why the job needed a person or an assistant with a browser.
This app holds a TMDB key, a cached client and the code that maps a show to
its TMDB id, so the titles come from there — `S05E01 - Futurama.mkv`
becomes `S05E01 Crimes of the Hot - Futurama.mkv`. Only files the script
itself named that way are touched, only when TMDB has that exact episode,
and a title it doesn't know is left exactly as it was. Subtitles carrying
the episode's code follow it.

**Look before you leap, and looking leaves no trace.** The preview is the
script's own `--dry-run`, which is nearly read-only — but items it skips
have a counter bumped in its state file, and at three it starts flagging
them as dead releases. Pressing a button to look should not age that
towards a false accusation, so the state file is put back byte for byte
afterwards.

Two bugs found by testing against a fake downloads folder, both in the seam
between the app and the script, both invisible to the scheduled task that
has been running this for weeks:

- **The script prints ⚠️, and a Windows python writing to a pipe encodes in
  cp1252.** It died on its own final `print` with every file already moved —
  the work done, the report lost, and an error where the report should be.
  It never showed up because the scheduled task runs in a Linux sandbox
  where stdout is UTF-8. The app forces `PYTHONIOENCODING=utf-8`.
- **The script ignores the directory it is run in.** `_find_root()` reads
  `TORRENTS_ROOT`, then falls back to a hardcoded `E:\Torrents` — so the
  first test, pointed at a sandbox, cheerfully operated on the real folder
  instead. Nothing was lost (there was nothing sortable in it) but the
  lesson is sharp: a working directory is not an instruction. The app sets
  `TORRENTS_ROOT` explicitly, which is also what makes the folder
  configurable at all.

The folder is offered rather than demanded: with none set, the app looks at
the parents of the library folders and suggests the one that actually holds
the sorter script — `E:\Torrents` here, since MOVIES and TV live inside it.

Tested end to end against a fake downloads folder with throwaway files: 16
checks covering the preview finding both items and routing them, the
preview moving nothing and restoring the counters, the real run moving the
film, stripping junk, quarantining extras, creating the show folder,
naming all three episodes from TMDB, adding the film to the spreadsheet,
leaving a `.part` file alone, reporting nothing on a second look — and the
real `E:\Torrents` untouched throughout, asserted at the end. Then the same
flow through the actual button in the browser: preview, SORT THEM,
progress, report.

Also removed the `__pycache__` folder in `E:\Torrents`, which the sorter
counted as an item and had been aging towards "no video file after 3 runs —
possible dead release", and dropped its entry from the state file. The
other counters were left exactly as they were.

---

## 2026-09-20 — v0.1.30, 615MB of somebody else's browser

Chasing a side question — what are "ProvenanceData" and "Edge Wallet"
inside `nextup_window`? — turned up more than the answer.

They are Edge's, not ours. `nextup_window` is an Edge *browser profile*,
created by the app-mode fallback that opens the page in Edge when
pywebview isn't installed (`--user-data-dir`), and Edge's component
updater fills any profile it is given with its own features whether or not
anything uses them: a 168MB ONNX vision model under ProvenanceData beside
a `techscam-detection-allowlist.json`, 200MB of downloaded component
packages, a 21MB Widevine DRM module, a payments wallet, a shopping
entity-extraction model.

**And the whole folder had been dead since 4 August.** Nothing had written
to it in six weeks: the window has been pywebview's for months, and the
`msedgewebview2.exe` processes running at the time belonged to Windows
Search rather than to this app. 586MB, deleted after a rename test proved
nothing held it open.

pywebview's own profile turned out to be the interesting part. It gives
the window a **fresh WebView2 profile in the temp folder on every run** —
five of them were sitting there, 71MB. The three untouched for two days or
more went; tonight's was left alone, as was one belonging to WinRAR.

That has a consequence worth more than the disk space: **anything the page
keeps in the browser is forgotten every time the app starts.** Only one
thing did — whether the queue panel is tucked away, added five days ago —
and it had been quietly resetting every night. It lives in
`nextup_config.json` now, beside the rest of the settings, through
`/api/queue/tuck`; `queue_state()` carries it back to the page. Checked by
tucking it, reloading, and finding it still tucked, then untucking and
finding that stored too. No `localStorage` anywhere in the page now, which
is the rule to keep: **this app's window has no memory of its own.**

The archive under `Old versions and extras` was left exactly as it is.
Pruning it would recover about 1.2GB, but those folders are there because
they were asked to be kept, and which of them still earns its place is not
a call to make on somebody's behalf.

---

## 2026-09-20 — v0.1.29, a sweep for dead weight

Asked for: tidying, with nothing changed about how the app behaves.

An audit of the file first — every function, constant and import checked
for whether anything references it, and every CSS class and id in both
embedded pages checked against the HTML and the JavaScript that builds it.
The Python came back clean: no unused imports, no unused constants, and
the only "unreferenced" functions were `do_GET`, `do_POST` and
`log_message`, which the server calls by name.

The stylesheet had seven classes for elements that no longer exist, each
left behind by a change that removed its markup:

- `.brand`, `.brandmark`, `.brand h1`, `.brand .dot` — the masthead's logo
  and 34px title, from before the facelift moved the name into the title
  bar.
- `.resumenote`, and the two media queries that hid it — including one
  added four days ago for the docked queue, which was carefully sizing a
  note that hasn't been on the page for a week.
- `.tmdbflag` and its `em`, plus its mentions in the facelift block and in
  the SELECT-mode hide rule.
- `.castfilms` and `.castfilmlink`, from an older cast panel.
- `.keys.four` in the remote.

And three loose ends of my own making: `recent_offers` and
`recent_offer_list` were the same query written twice (now one calls the
other); the right-click menu still carried the plumbing for the grey hints
that were removed from it in v0.1.26, passing an empty string at all six
call sites; and a comment still described the count on "the Queue tab",
which existed for about an hour before becoming the side panel.

1,902 bytes lighter, 324 classes down from 332, and the audit now reports
nothing dead in either page. Verified by re-running it, both test suites
(19 and 10), and the app itself: every tab drawn, the right-click menu
intact at its six items, the queue still working, no console errors, and
the Library's first poster at exactly the same 185px it was before.

`__pycache__` went from the app folder too — a by-product of running from
source, which Python writes again on the next start.

---

## 2026-09-20 — v0.1.28, "the port is still in use"

Reported as: after closing the app it takes a while before it will start
again, because it says the port is in use.

It was telling the truth, and the message was still wrong. `port_in_use`
asks by connecting rather than by binding — deliberately, see the note on
it — so a positive answer means something really is listening. Nothing was
stuck: closing the window is simply not the end of the process, and the
server went on holding the port through everything that came after it.

What comes after it, timed: asking mpv to quit and waiting for it, which
on a channel is a `taskkill` with a five-second grace; closing the books on
what was playing; then writing the TMDB cache — **66MB, about a second and
a half, written on every close whether or not a single lookup had
happened**. In the worst case that is the best part of seven seconds of the
port being held by an app with no window.

Three fixes, and the first is the one that matters:

- **`release_port()` runs first, on the window's `closing` event.** The
  server is shut down and the socket closed before any of the tidying up,
  because none of that needs a server. Measured end to end with a channel
  playing and a dirty cache: the port is free **0.22s after the click**,
  and the remaining 6.9 seconds happen with it already free.
- **The cache is only written when it has changed** (`_CACHE_DIRTY`). An
  evening of browsing a library that was already scanned now writes
  nothing at all on the way out.
- **A copy started too early waits instead of refusing.** If the port is
  held but doesn't answer as this app, that is almost always the copy you
  just closed, so `wait_for_port` gives it ten seconds before the error
  box. The error text now says "still using" rather than "already using",
  because by then it really is something else.

One non-daemon thread went with it: the browser-fallback path's
`threading.Timer` that opens a tab after a second. It was never the reason
for this — it fires and dies — but a non-daemon timer is a thread that can
keep a process alive, which is exactly the family of bug being fixed.

Tested at three levels: the pieces (10 checks — the port frees, frees
quickly, a new server can bind straight away, calling it twice is
harmless, waiting gives up only when something really holds it, an
unchanged cache isn't rewritten); the whole close sequence on a spare port
with a channel "playing" (5 checks); and the existing queue suite for
regressions. A test failure along the way was the test's own fault and
worth remembering: a raw `listen(1)` socket that never accepts starts
refusing connections once its queue fills, so it looks like a free port to
anything that probes by connecting.

What is still outside our hands: WebView2's own teardown after the window
goes. It no longer matters, because the port is released before it starts.

---

## 2026-09-20 — v0.1.27, what "Pick something" was really offering

Asked for: measure whether some films come up more than others. They did,
and one of the reasons was a bug.

### Measured first

Two instruments, both in a sandbox against a copy of the library. The exact
odds of every one of the 599 eligible titles being the card on one press,
worked out from the three branches of the draw rather than sampled; and
3,000 presses through the real endpoint path with the 150-press memory
running, which is about a year of evenings.

The memory was doing its job — 534 titles seen, nothing repeating inside
150 presses. Underneath it the ranking was not:

- **71% of presses went to the 168 titles TMDB rates 8.0 or better.** The
  score started life as the raw TMDB rating, so an 8.6 began 1.6 ahead of a
  7.0 and nothing the app knew about the user could close that.
- **A cliff at #48.** Only the top 48 unrated films entered the weighted
  draw. North by Northwest at #48 was one press in 109; To Kill a
  Mockingbird at #49, the same TMDB 8.0, separated by a tie-break, was one
  in 2,396.
- **12 Angry Men was one press in 19** against a fair share of one in 599,
  and with the memory on it came back like clockwork every ~155 presses.

### The bug: a show you're watching is not a rewatch

The draw kept ratings-you-own in a separate reserve of twelve per type, so
a loved rewatch couldn't crowd out the pile you haven't got to. Sound for
films. For television it was wrong, because **rating a show you are in the
middle of doesn't mean you have finished it** — and thirteen of the shows
in the middle of their run were sitting outside that reserve at one press
in 2,396: Seinfeld at S09E17, The Simpsons at S07E16, It's Always Sunny,
Peep Show, Arrested Development, Nathan for You. The shows on most
evenings were the hardest ones in the library to be offered, and their
"pick it back up" bonus never counted for anything because they were in no
ranked pool at all.

What counts as a rewatch is now decided where the pick is built and
carried on it, rather than inferred from `userrating` inside the draw: a
film you've rated, or a show you've rated and are NOT part way through.

### And a signal that was missing entirely

Every input was an opinion — TMDB's rating, your rating, the watchlist.
Nothing said which programmes you are *watching*. `show_watch_habits()`
counts episodes played per show over 90 days, straight from the history,
worth up to 2.0 and diminishing, so the current rotation outranks a show
rated once and untouched since, and fades on its own when you move on. The
card says so: "64 episodes in the last 90 days · S04E16 is where you got
to".

### Three tunings, and one that had to move with them

`TMDB_WEIGHT` 0.35, measured from 6.5 rather than zero. `RANK_SOFTNESS` 3
→ 10, and the 60-per-type cut-off removed entirely, so the whole shelf is
in the draw on a gentle slope instead of a short list with a cliff at the
end of it.

Then the watchlist. Its 0.6 was tuned against a *raw* TMDB rating; against
a weighted one it was worth nearly five points of TMDB, and the check
afterwards found **eleven of the top twelve films in the draw were
watchlisted** — the "watchlist, in order" failure of the 2.5 bonus,
reached from the other side. Retuned to 0.35, where it is worth about one
point of TMDB, and the top of the list interleaves again. The two numbers
have to move together; the note on WATCHLIST_BONUS says so.

### The trap the other fixes set

With in-progress shows ranked properly, the offer memory had a hole in it:
it holds back the EPISODE, and the next episode of the same show is a
different key — eligible immediately, and ranked just as highly. A show
being binged would have taken over the Now tab. `SHOW_COOLDOWN` holds a
whole show back for 15 presses, narrowing along with the memory when the
filters are tight. Verified by show id over 600 presses: no breaches.

### After

| | before | after |
|---|---|---|
| presses going to TMDB 8.0+ titles | 71% | 48% |
| likeliest title vs least likely | 336x | 47x |
| top 10% of titles take | 64% of presses | 36% |
| distinct titles in 3,000 presses | 534 | 576 |
| never offered at all | 65 | 23 |
| shows you're part way through | 13% of presses | 17% |
| busiest title | 12 Angry Men, 19 | The Simpsons, 16 |

The top of the list is now Cowboy Bebop, Futurama, South Park, Seinfeld —
the things actually being watched — at around one press in 60 to 100 each,
rather than 12 Angry Men at one in 19. Checked across every filter
combination the page offers, including the tight ones where the cooldown
has to be given up: Documentary under 100 minutes still answers 40 presses
out of 40 from a shelf of ten.

Worth knowing for next time: the audit reported a show repeating two
presses apart, which looked like a cooldown failure and is the **X-Men '97
duplicate** in the Planned section at the top of this file — two show rows
with one name, so measuring by title counts them as one show and measuring
by id doesn't.

---

## 2026-09-18 — v0.1.25, a queue, and a Now tab with no gap in it

### Right-click, and a queue down the side

Asked for: posters you can right-click, with Play next and Add to queue as
two separate things, plus favourites and watchlist. Then, part way through:
show the queue down the right of the window, the way a player keeps its
playlist beside the picture.

The menu is one element for the whole page, rebuilt on each open because
its words depend on the thing — "Remove from favourites" only means
something on a favourite. Play, Play next, Add to queue, the two flags,
Open. It flips left or up near the window's edges, closes on anything else
(a click away, Escape, a scroll, the window losing focus), and takes the
arrow keys. Favourites and watchlist from the menu update the poster's
badges and the hover panel's buttons through one `_refresh` on the tile,
so the two ways in can't disagree.

**The queue lives in the database**, in its own table, so one built on
Friday is still there on Saturday. `pos` is a REAL so Play next can go in
front of the head without renumbering everything behind it.

**A show is an episode by the time it's queued**: the one you're up to,
the same answer the Now and Rate tabs give. Queue Seinfeld again and you
get the episode after the last one already queued, rather than the same
one twice — which is what "queue three episodes" means to anyone doing it.

**It moves on only when something finishes.** The hard part, and it came
down to one fact about mpv: a film was launched to close itself at the
end, and an mpv that has exited looks exactly the same whether the film
ended or you shut the window. Only one of those should start the next
film — a queue that marched on after you closed the player would be
playing films to an empty room. So while anything is queued, films are
launched (or switched on the spot, if the queue grows mid-film) to hold
the window open at the end instead, the way channels already do. Idle is
unambiguous; exit isn't. With the queue empty, a film closes itself at the
end exactly as before.

Precedence, decided rather than left to fall out: a **channel ignores the
queue** (it's its own schedule, and the queue waits until you're back on
something you picked); a **queue beats an episode's next episode** (you
asked for this next). Skipping to something in the queue closes the
outgoing sitting with where it got to, so History doesn't show two things
playing at once. A queued file that's gone missing is dropped, not played
as an error. The remote's SKIP, which only ever worked on channels, now
also means "next in the queue".

**The side panel** replaced a Queue tab in the Library that lasted about an
hour — it was the right call to make the queue visible from every tab,
since what's next isn't a Library matter. Three states, one at a time:
docked beside the page (the body gives up 300px and the page re-centres in
what's left), overlaid across the page's right edge, or tucked into a tab
on the window's edge with the count on it. Below 1100px docking would
squash the Library, so it starts tucked there and slides out over the page
when asked. Tucking by hand is remembered; the width only decides docked
versus overlay, and it's told through `matchMedia` because resize events
arrived before the new width did and left the panel docked one resize too
long.

Docking exposed an assumption running through the page's CSS: **every
width rule measured the window, and the page is no longer the window.**
Two fixes, chosen for different reasons. The header's two navs moved to a
container query on the header itself — not on `.wrap`, because a size
container becomes the containing block for fixed-position children, and
the title bar and every sheet live in `.wrap`. The Library toolbar's four
rules couldn't do the same: the page column stops growing at 1120px, so a
container rule would change what happens on every window wider than that.
Those are mirrored at +300px under `body.queue-docked` instead, so an
800px page behaves the same whether the other 300px is a queue or nothing.
Measured docked at 1400, 1100 and 1099 (the switch), overlaid at 760:
header on one line, toolbar on one line, nothing under the panel, no
sideways scroll, and Now, Rate, Channels and Settings all fit beside it.

### The next pick, fetched before you ask

Reported as: the picture behind a pick sometimes takes a moment to pop in.
It did, every time — the card was drawn the moment the pick arrived and
only then did the browser start downloading the backdrop.

So while you look at one pick, the next is already drawn and its backdrop,
poster and reasons downloaded. It's keyed on everything the draw depends
on — the three filters and the set of things turned down, including the
one on screen, since pressing the button adds it — so a filter change
discards it and draws fresh. With nothing fetched ahead (the first pick, a
new filter) the card waits up to 700ms for its picture and no longer.

One server change was needed to keep the anti-repeat memory honest: a pick
fetched ahead may never be shown, so `/api/tonight?peek=1` doesn't count it
as offered, and the page reports it through `/api/offered` when it actually
goes on screen.

Measured: eight presses at a normal pace, every swap 6–7ms with the
backdrop already in the cache and the reasons already there. Pressed as
fast as it will go, 110–185ms each — waiting for a look-ahead still
downloading rather than showing a card without its picture.

### Something my own tooling broke, now fixed

While chasing two failures in the sync test, the real config turned out to
have sharing switched **off**, while still recording that it had been
sharing to OneDrive — and the PC's shared file hadn't changed since 22:44
on 14 September, minutes after sharing was first switched on.

The cause was the dev server used for browser testing. It ran against a
copy of the library but still wrote settings to the real
`nextup_config.json`, and it blanks `sync_folder` so a test can't write to
OneDrive. Clicking through the profile picker in a browser test saved that
blank over the real settings. Sharing was turned back on through the
running app itself — so its in-memory settings agree and won't write the
blank back — and it caught up at once, the shared file going from 624KB to
649KB. The dev server and the test scripts now redirect every file the app
writes (settings, recommendations, play state, resume folder, error log)
and refuse to start if any still points into the app folder. After the
change both suites were run with the real files fingerprinted before and
after: untouched.

The same investigation found two test failures that were artefacts, not
bugs: both simulated computers start from a copy of one library, whose
history now carries the uids it was shared under, so the copies deduped
against each other. Two real machines never share uids; the test's second
computer now forgets them first, and it's back to 27 of 27.

---

## 2026-09-17 — v0.1.24, two more ways to fill the shelf

Asked for: a section of TV shows I might like, a section for things that
would be good on the channels, and a look at the page itself.

### Shows you might like, from your TV taste and not your film taste

The existing "For you" learns from films: it reads every film you've rated,
weights each one's keywords, cast and director by how far your score sits
from your own average, and searches outward. It has never read a show, and
pointing it at television would have been wrong anyway — the person who
rates crime films highly may watch nothing but sitcoms, and those are two
different tastes wearing one name.

So the new section anchors on **your own shows**: anything scored above your
midpoint, or marked a favourite, becomes a "more like this" seed, and the
genres those shows carry — weighted by score and tempered by how many back
them up, the same shape as the film profile — drive a few searches of their
own. The film profile's strongest *themes* are borrowed as a third anchor,
because a keyword means the same thing on either side of TMDB: "time travel"
says as much about a show as about a film. Names and people don't cross over
and aren't asked to.

TV needed its own vocabulary in two places. TMDB keeps a **separate genre
list for television** — "Action & Adventure" and "Sci-Fi & Fantasy" are one
tag each there and don't exist on the film list — and it is the list the
library's own shows were tagged from, so `tmdb_tv_genre_names` sits beside
the film one rather than reusing it. And a TV row calls its title `name` and
its date `first_air_date`, so `_tv_item` converts one to the other and the
cards never learn the difference. The hover panel asks `/api/brief?kind=tv`
and gets **who created it and how long the run is** — 5 seasons · 62
episodes — where a film gets its director and its runtime.

Forty shows came back on the real library, led by things that hit several
anchors at once: The Owl House (comedy + animation + a seed), Close Enough
(three shows you rate), King of the Hill (The Simpsons and one more).

### What would fill your channels

The idea this one earns its place on: **a channel with twenty hours of
programmes loops them all week, and nothing anywhere said so.** So the
section measures every channel first — through `channel_blocks()`, the same
function the Channels tab schedules from, so the numbers are the channel's
real ones — and leads with the thinnest. In Black & White has **10
programmes, 20 hours**; Comedy has 1,339 and 697 hours. Under a day of
material is marked THIN, because that is where a channel comes round again
inside a day and anyone who leaves it on will notice.

Then, per channel, what TMDB has that **that channel's own rule would pick
up the day it arrived**. Each channel's filter is translated into a discover
search — genres as an OR, `require_genres` as an AND, excluded genres as
`without_genres`, a keyword channel resolved through `/search/keyword` — and
the parts discover cannot say are done afterwards on the results, because
there is no "not in English" and no "not from Japan" in its vocabulary. The
five personal channels are skipped outright: Favourites, Watchlist and Binge
are things you marked, and no search can suggest one.

Three passes of tuning, each from looking at what came back:

- **The budget went to the wrong channel.** Saturday Morning and All Day
  Daytime are named lists, and a named list is one lookup per title — ninety
  of them. Walked in channel order they ate the entire allowance and the
  other twelve channels got nothing. The discover searches now run for every
  channel first (about 25 calls), and what's left goes to the lists, eight
  fresh titles per channel per scan. Cached lookups are free, so the lists
  fill themselves in over a few scans.
- **Sorted by score, discover's first page is not what you want.** It is
  whatever a few hundred devoted people rated 9 — fan-club cinema, and a
  new release at 8.9 off its first thousand votes, which drifts down all
  year. Floors went up to a thousand votes, and nothing from the last
  eighteen months is offered at all. Cult Classic, whose own rule has no
  vote floor, needed one here for the same reason.
- **"Hide the obvious" is now asked of TMDB as well.** Top Shelf is films
  over 8.0 with thousands of votes, so the page filter threw away almost the
  whole result set and the channel came back with a single suggestion. With
  the cap in the query it gets twelve.

All fourteen eligible channels now come back with a full list — Harakiri and
Modern Times for In Black & White, Planet Earth and Cosmos for True Life,
Batman: The Animated Series for Saturday Morning off its own named list.

### The page

The counts hub used to be a grid of large panels under a full filters band,
which put two rows of chrome between the sub-nav and the first suggestion.
It is one row of seven compact counters now, above them a single bar
carrying the action, when it last ran, and the two switches that apply
everywhere. The first section heading starts at 306px of a 1200x850 window
with all of that above it. Seven across is 144px each at full width; below
about 900px they wrap to a second row rather than shrink.

Smaller things the new sections forced: cards say the genre next to the year
and wear a **TV** flag when films and shows share a grid; the taste profile
panel folds shut, since it is the working-out rather than the answer; reason
chips stopped being lowercased, because "like arrested development" reads as
a typo where "like Arrested Development" reads as a sentence; and the empty
state says what pressing the button will actually produce instead of naming
the button again.

Checked in the browser at 1200 and 760: no console errors, nothing
overflowing sideways, HIDE works on a show, on a channel's single pick and
on a whole channel, and each one takes the hub's counter down with it.

---

## 2026-09-14 — v0.1.23, the header gives back a row

Asked for as three moves. The version-and-counts line went up into the title
bar beside the name, where the strip had room going spare. The Library's
section tabs (Films through Drives) moved up onto the same line as the main
tabs — still their own control on the left, the main pill on the right, and
shown only while the Library is. And the main tabs got air above them: with
the counts line gone they sat hard against the title bar's divider, so the
masthead has 12px of top padding and a smaller gap below it.

The section tabs hide with `visibility`, not `display`, when you leave the
Library. The main tabs are pushed right by `margin-left:auto` and wouldn't
move either way, but a hidden element that still holds its width is the one
that can never make them jump if that ever changes.

Two navs on one line is about 960px of words, and a wrapped line would hand
back the whole row this was meant to save. So they tighten in steps as the
window narrows (1100, 900 and 800px), and were measured on one line at 1200,
1105, 1000, 900 and the window's own 760px minimum. The first of those steps
didn't take at first: the facelift's later `.tab` padding outranked a bare
`.tab` in a media query, which the measurement caught (still "8px 16px" at
760) and a longer selector fixed.

---

## 2026-09-14 — v0.1.22, one history across computers

### Sharing through a folder someone else keeps in step

Asked for: history shared between the PC and the Mac, as automatic as it can
be, and then — agreed in passing — ratings, the watchlist and favourites with
it. Done through a cloud folder (OneDrive by default) rather than anything
online of our own. No server to keep up, no account, no login — and the
note on the profile picker already argues why a login this app can't back up
would be worse than none.

**Each computer writes only its own file.** `Next Up sync/device-<id>.jsonl`,
one event per line, appended. That is the whole reason it can be left
running unattended: two machines never write the same file, so OneDrive has
nothing to reconcile and never produces a "conflicted copy" with half of
someone's evening in it. The obvious alternative — the library database in
OneDrive — is the one thing never to do: a sync client copying an SQLite
file mid-write is a corrupted library, and two machines writing it is a lost
one.

**Events, not state.** "Rated 8 at 21:04" can be merged; "the rating is 8"
can't, because nothing says which computer said it last. Where two computers
disagree the later event wins, compared in UTC — `at` is written in local
time and stops being comparable the moment a clock changes. Clearing a
rating or taking something off the watchlist is an event too, so an undo
travels like anything else. Ties keep what's here, so two machines can never
swap values back and forth.

**Keyed by TMDB id**, plus season and episode, for the reason the snapshot
work already wrote down: a row id is different on every machine and a title
match is worse than none. Every history row now records that identity when
it's written, since the id it points at means nothing elsewhere.

**Applying an event never calls log_event.** One rule, and it is the one that
stops a rating echoing between two computers for ever. Every event also
carries a uid, so a file read twice, rewritten, or duplicated by a sync
service adds nothing — checked: six further rounds, both files byte-for-byte
unchanged, no duplicate rows.

**The trap, found by reading rather than testing.** A resume position can't
just be written onto the row. `sync_playback_state` reads a library position
with no mpv watch-later file behind it as a film you *finished* — so a
position from the Mac would have turned into a play on the PC the next time
mpv touched its folder. The position is written into mpv's own file too,
named as mpv names it (the MD5 of the path, checked against the files it had
written here), keeping any volume or audio delay already saved in it. When
the other computer finishes a film, the row is cleared *before* the file is
removed, so there's no instant in which that same rule could fire.

**What this computer already had** — ratings older than the history table, a
watchlist from the first week — has no event to share. The first share
describes it as seed events dated by their own timestamps. Seeds set state
elsewhere but never appear in a History, because they didn't happen then;
their uids are made from what they say, so re-sharing an unchanged library
adds nothing.

**History knows where an evening happened.** Rows arriving from elsewhere
carry the device's name; a sitting is only closed by an ending from the same
computer, so "played" on the Mac and "stopped" here stay two evenings. A
film only the other computer has still gets its row, marked with where it
was watched and without buttons, and waits in the inbox to be applied if a
scan later brings it in.

On the way: `build_history` read `ORDER BY id ASC LIMIT n` — the OLDEST rows,
and in row order rather than time order. Harmless while rows were only ever
written as things happened and the table was short; neither is true once
another computer's history lands in it. It reads the newest now, by time.

**What it can't control, and says so.** A OneDrive folder is still a folder
when OneDrive isn't running; events land in it and go nowhere. Settings
checks for the client and says plainly when it isn't there — which is true
of this PC as it stands: the folder exists and OneDrive.exe is not running.
An unreachable folder loses nothing: `shared` stays unset and the rows go out
when it's back.

Tested as two computers on one machine — two copies of the app, each with its
own copy of the library, sharing a scratch folder — 27 checks: rating one way
and the other, the later of two conflicting ratings winning on both, a clear,
watchlist and favourite, a stop at 40:19 resuming on the other side with
mpv's file written and the resume-folder check leaving it alone, finishing it
clearing the other's position and counting a play, a half-written line left
for the next pass, a film only one side owns, a deleted device file rewritten
whole with no duplicates on the other side, and stop-sharing leaving the files
alone. Not tested on the Mac itself: the folder detection there
(`~/Library/CloudStorage/OneDrive-*`) is written from where OneDrive puts it,
not from having seen it.

---

## 2026-09-14 — v0.1.21, the Mac work comes home

No new features: this is the Mac version brought back to the Windows
machine and made the one copy. The version moves on because the frozen
NextUp.exe that travelled with the Mac folder was still the 0.1.20 build
from before the port — same hash as the one left behind — so a number that
didn't change would have hidden exactly the thing the note above warns
about, a frozen build and a live script that had drifted apart. Rebuilt from
this source.

Checked on Windows before anything moved, against a copy of the library in a
scratch folder: the new tables (`profiles`, `ignored_files`, the four
`snapshot_*`) created themselves on the old database without disturbing a
row — 538 films, 75 shows, 2,053 episodes before and after — the page script
parses, the drive catalogue still reads G:, mpv answers, and the Now picks
come back. The Windows library has no profiles yet, so the first start here
opens on the new who's-watching screen.

**The mac/ folder did not come across intact, and is not in this one.** The
bundled CPython is full of symlinks, and unpacked on Windows each became a
nine-byte text file holding the link's target — `bin/2to3` is literally the
word "2to3-3.12". It would look complete and fail on the first double-click.
The Mac copy is the zip as brought home, which keeps its links; unpack that
on the Mac, not this.

The folder itself was tidied at the same time: the current version at the
top level, and every older build, zip, the 0.1.1 package folder, the release
staging and the one-off rescue script under `Old versions and extras`. The
live data never moved — the source copy and the exe now sit side by side
and share one library, where before the package folder had a config of its
own and no library.

---

## 2026-09-13 — the Mac port, and carrying a library between devices

### A sitting nobody closed never happened

Reported as: why isn't the Cowboy Bebop session in History? It was in the
table the whole time —

    2026-09-13 21:59:33  movie  126  Cowboy Bebop: The Movie  event='played'

— and `WATCH_EVENTS = ("watched", "stopped")` is what build_history read.
A sitting STARTS at "played" and ends at one of those two, so reading only
the endings drops every sitting that never got one. The app being closed
mid-film is the ordinary way that happens, and it had happened, repeatedly,
while this was being worked on.

Those are kept now, marked open, and speak through the library's own
resume position — mpv wrote 2419s of 6900s before the app went away, so
"got to 35%" survives even though the ending never landed.

### History merges by thing and keeps its sittings

Asked for, and it reverses a decision this file used to defend: build_history
said "not grouped and not deduplicated ... watching the same episode twice
in a week is two evenings and the history should say so". Right about the
facts, wrong about the page — a rewatched show became a wall of one title.
One row per thing now, every sitting inside it behind a "5 sittings"
expander, each with its own date and how far it got. Nothing is lost.

The headline numbers on a row describe the LATEST sitting, because "got to
35%" is a fact about an evening rather than about a film.

One thing the test data caught that the code had asserted otherwise: I wrote
"an open sitting is always the latest". The Iron Giant had FIVE sittings,
three of them open, which disproves it on sight. Only the newest may borrow
the library's resume position — that position describes the last evening and
nothing about the three before it.

OPEN became MORE on the row buttons, as asked.

### Closing the app left mpv running

mpv is an ordinary child process and nothing ended it, so closing the window
left a player going with nothing driving it — and the sitting it was in the
middle of never got an ending either. One missing step, two symptoms.

shutdown_playback() reads the position while mpv is still there to ask, then
stops it politely so --save-position-on-quit still fires, then closes the
books with "closed" rather than "ended" — "ended" means the programme
finished and is the cue to start the NEXT episode, which is not a thing to
do on the way out.

Getting it to run on a signal took three attempts and the first two are
worth keeping here, because both looked correct:

  1. atexit. Does not run on SIGTERM at all; the process is simply taken
     down.
  2. A signal handler calling sys.exit(). Python runs handlers on the MAIN
     thread between two bytecodes, and this main thread spends its life
     inside the GUI's own C event loop — so the handler got no turn, and
     when it eventually did there was nothing for SystemExit to unwind. The
     app went from ignoring SIGTERM to ignoring it harder: the next pkill
     couldn't kill it either, which quietly meant a later test ran against
     the stale process and reported a pass that wasn't one.
  3. signal.set_wakeup_fd. The C-level handler writes a byte to a pipe
     whatever the interpreter is busy with, and a thread of ours sits on the
     other end. That works.

Belt and braces: pywebview's own `closing` event also calls it, which is the
path Cmd+Q and the window's close button take, and shutdown_playback only
does its work once however many of them fire.

### One card, and History as the place the rest of them live

The four-wide resume grid was reserving space for three cards that usually
aren't there — which is what the dead strip to the right of the poster
actually was. The Library keeps ONE: the thing you were halfway through is
a reminder, not a list. The heading became a button and goes to History,
which is the full list it was the first line of.

That freed the rest of the line for the toolbar, so the strip moved INSIDE
.libtop as a left-hand column. Worth noting because it deleted code rather
than adding it: the divider is one ordinary border on one element again.
The previous round had a `:has(+ .resumestrip:not(.hidden))` rule handing
the line back and forth between two siblings, plus a media-query override
that had to repeat the selector exactly to win on specificity. All of that
goes when the two things are in the same box.

The count gives way at 1340px now rather than 1000px: the card takes 262px
off the toolbar's line, and a wrapped toolbar costs 41px of poster grid to
keep a number the pager already shows.

First tile at 298 of a 900px window — 33%, from 43% when this started. At
760x600 the left column drops entirely and it's 263.

### History does things now

It was a record you could only read. Every row that still has something
behind it gets RESUME (or WATCH AGAIN, if you finished it) and OPEN.

Two things the API had to learn, both of them consequences of the note
already at the top of build_history — history outlives the files it is
about:

  available   whether the thing is still in the library at all. A PLAY on a
              row whose file was deleted is a button that can only
              apologise, so those rows keep their record and lose their
              buttons.
  show_id     an episode has no page of its own; the library page it
              belongs to is its show's.

The buttons are visible at rest rather than on hover. A control you can
only find by waving the mouse at it isn't a control, and the point of the
change was that the page can be acted on.

### The divider ended up inside the thing it was dividing

The rule under the old search row separated the header from the grid. With
the heading moved up onto that line, the rule ran between "Continue where
you left off" and the card that heading is about — so the card read as
belonging to the posters below rather than to its own title.

It belongs under the WHOLE header, so it moves: `.libtop:has(+
.resumestrip:not(.hidden))` drops the border and the strip takes it, and
when there is no strip — searching, or nothing to resume — the toolbar keeps
it. Costs nothing in height; the first tile stayed at 309.

The short-window case needed care and would not have been caught by looking
at it. `max-height:700px` hides the strip with `display:none`, which does
NOT add `.hidden` — so the `:has()` rule still believed a strip was
following and handed the line to an invisible element, leaving the header
with no divider at all. The override inside the media query then lost
anyway, because a media query adds no specificity and
`:has(+ .resumestrip)` scores below `:has(+ .resumestrip:not(.hidden))`.
The selectors are now repeated exactly so source order settles it.

### 43% of the window spent before the first poster

Reported as tiles sitting in the bottom half with dead space to the right of
them. Measured at 1200x900 the first tile started at y=388 — 43% of the
window gone before a single piece of artwork — and the search box was 556px
of a 1072px row with 516px of nothing beside it.

Two full-width bands were stacked where one line would do. The resume strip
is a FOUR-column grid (deliberately: there is a note above it explaining that
auto-fit was letting the cards wrap and doubling the strip's height), so a
single resume card occupies a quarter of the row and leaves three quarters
empty. Underneath it the search row spent another 99px, its three controls
each carrying a stacked label costing ~20px of height to say one word.

The heading and the whole toolbar now share one line, with the resume cards
below on their own. Getting the toolbar onto ONE line was the entire game —
it wraps at 41px a time and a wrap gives back everything the restructure
won:

  - the "SEARCH" label went, since the input's placeholder already reads
    "Title, director, actor or genre"; it is still there for a screen reader
  - the selects are capped at 118px rather than sized to "Part way through",
    a width they show about a fiftieth of the time
  - the resumenote ("picks up where you stopped") repeats the heading beside
    it, and hides below 1440px where the toolbar needs the 183px more
  - under 1000px the count goes too: the pager already says "1-120 of 125"

Result at 1200x900: first tile at 308 instead of 388, 34% instead of 43%.
At the window's own 760x600 minimum, 266 instead of ~347, toolbar still on
one line. Searching pushes it to 225, because the strip hides and the
toolbar takes the whole width on its own.

One trap in the split, found by measuring rather than by looking: the
heading used to live INSIDE .resumestrip, and there is a `max-height:700px`
rule that hides the strip entirely on a short window. Moved out, the heading
survived that rule and kept its 227px — which pushed the toolbar onto a
second line and cost more height than hiding the strip had saved. The rule
hides both now.

### Seinfeld's last four episodes were sitting in the film library

Two tiles with no artwork, no year and no idea what they were: "921 & 922 -
The Clip Show" and "923 & 924 - The Finale". Both real files, 1.2GB and
1.7GB, in TV/Seinfeld (1989)/Season #9/ — the show's last four episodes as
two double-length files. The other twenty in that folder are named
"S09E01: The Butter Shave - Seinfeld.mkv" and matched perfectly; these two
use a different convention and fell all the way through to being films.

TWO faults, and the first hid the second.

`_SEASON_DIR_RE` was `^(?:season|series|s)[\s._-]*(\d{1,2})$` — no "#".
`_SEASON_PREFIX_RE` one line below it already allowed "#". So "Season #9"
was a season folder to one test and not to the other, and the
"Season 3/07 - Title.mkv" fallback never ran at all here.

With that fixed it still got them wrong: "921" read as episode 921. That
number is the season and the episode written together, a convention the
codebase already knew about in `_CAT_EP_NUMBER` but not in `parse_episode`.
It now splits the leading digits ONLY when they start with the season the
folder already established and what remains is 1-99 — so "300 - Title.mkv"
in a Season 3 folder stays episode 300 rather than quietly becoming episode
zero. Eight cases checked before the library was touched, including that one
and a two-digit season ("1004" in Season 10 -> E04).

Both now land as S09E21 and S09E23, Seinfeld is 78 episodes instead of 76,
and the film library is two phantom entries lighter.

The remaining limitation: one file holding two episodes is filed as the
first of the pair, so E22 and E24 read as absent. There is no
multi-episode-per-file concept in the schema and inventing one for four
episodes would be the wrong trade.

### The duplicates panel asked the question backwards

Found by watching it used rather than by testing it: the 2160p Parasite was
removed and the 2.2GB 1080p kept — the opposite of the stated intent, and
the opposite of what the panel itself recommended.

The cause is a UI fault, not a mis-click to shrug at. The radio marks the
copy to KEEP, while the buttons act on everything else. Clicking the file
you want rid of therefore does precisely the reverse, and nothing on the row
you clicked said so. Every row now states its own fate — KEEP THIS or GOES,
with the doomed rows dimmed — and the button counts what it is about to do.
The state was visible only after the press; now it is visible before.

### Duplicates, and why "keep the bigger one" isn't a rule

Asked for as a function beside the refresh arrow: find films held twice and
deal with the files, keeping the larger as the better copy.

The instinct is right and it is not sufficient, which this library proves on
its own. There are two duplicate pairs in it. Parasite is a 2.2GB 1080p and
a 6.5GB 2160p — the rule works perfectly. The Big Lebowski is
**4,946,508,193 bytes and 4,946,508,193 bytes**: the same number twice, one
file copied under two names. A size comparison there picks one at random and
presents it as a decision.

So the ranking is resolution first and size second, and it withholds a
recommendation when the top two are the same size to the byte — `too_close`
on the API, which the page renders as a question rather than a suggestion.
A first pass also managed to print "1080p beats 0p", because an untagged
filename parses as height 0. Unknown is not worse; heights only decide
anything when both files declare one.

**Removing from the library needs somewhere to remember it.** Deleting the
row alone is undone by the next scan, which walks the disk and finds the
file exactly where it was. Hence ignored_files, checked in walk_media —
the one choke point every scanned file passes through — and cached for five
seconds because a scan asks it thousands of times.

**The bin, never unlink.** A wrong call costs a file that took an hour to
fetch, and the whole point of a recycle bin is that a wrong call survives
it. SHFileOperationW with FOF_ALLOWUNDO on Windows; on macOS the volume's
own .Trashes rather than ~/.Trash, since moving five gigabytes to the home
Trash means copying it across a USB cable in order to delete it. The file
goes first and the row goes only if that succeeded — a library that has
forgotten a file it failed to delete is worse than one that never tried.

And the honest limitation on this machine: the films live on an NTFS drive,
macOS mounts NTFS read-only, so MOVE TO BIN cannot work here at all. It is
disabled with the reason shown rather than failing on click. The Windows
side is where that button earns its keep.

Verified end to end on the real library: the 1080p Parasite removed, a full
rescan run, and it stayed out — then restored, and the library is back to
129 films exactly as it was.

### The profile picker, built as a front door and not a lock

A profile is a person; the device is derived. Those are different axes and
the picker keeps them apart deliberately — conflate them and one person
across two machines becomes two people with half the ratings each, which is
the X-Men '97 split under another name. The machine gets its own name on the
same screen, because that name has a real job: it travels inside an exported
snapshot and is what the other device prints on every greyed poster.

The first profile seeds from the ACCOUNT's name, not the hostname. Seeding
"Someones-MacBook-Pro" as a person teaches exactly the wrong model on the
one screen whose whole purpose is to distinguish the two.

`separates_data` is a flag on the API rather than a sentence in the page.
Ratings still live on the item rows, so the picker says they are shared;
when the migration happens the flag flips and the wording follows it, rather
than a claim in prose quietly going stale.

It is one window, not a separate process. The original idea was something
running before the app opens, but a screen shown before the library is the
same experience without a second process to keep alive, crash, or explain —
and it sits BELOW the title bar, so the window still closes while nobody is
chosen.

Still to do: `profile_id` on ratings and history, with a migration putting
every existing row on profile 1.

### The app was called "python", and had no icon

A bare interpreter has no bundle, and macOS names a process after the
executable it launched — so the menu bar said "python" and the Dock showed
the generic rocket. Nothing in pywebview fixes that, because it is not
pywebview's to fix: the name and the icon come from the bundle, or from
nothing.

So there is a real Next Up.app now: an Info.plist with CFBundleName,
CFBundleIdentifier and an icns built from nextup_logo.png with sips and
iconutil, both of which ship with macOS and need no Xcode. The bundle's
executable is a three-line shell script that resolves HERE to the folder
the .app sits *in*, not the bundle's own insides — the database, artwork and
settings stay beside the app exactly as the README promises, rather than
being swallowed by a bundle that an update would replace wholesale.
`lsappinfo` now reports LSDisplayName "Next Up" against uk.co.nextup.app.

Next Up.command stays, and is worth keeping: a .app has nowhere to show a
startup error, and the terminal version does.

### keep-open=yes, which I put there and which broke playback

Added to mpv.conf with a comment claiming it let "the app's own what's next
logic decide". That reasoning was backwards. mpv_play already says it
plainly — a channel wants the window held open, "something picked by hand
doesn't: when it's finished, it's finished" — and the app expresses that by
passing --idle per playback, never --keep-open. The monitor then watches for
mpv either exiting or going *idle*, and idle is the cue to start the next
programme on a channel.

A global keep-open=yes defeats both halves: a hand-picked film hangs on its
last frame instead of closing, and a channel never reaches idle, so the next
programme never arrives. That is the README's own "a channel stops after one
programme", reintroduced from the config file. Removed, with a note in
mpv.conf saying why nothing should put it back.

### shut() closed a window, not the app

`webview.windows[0].destroy()` ends the main window. The GUI loop runs until
every window is gone, and the remote is a window — so closing the main one
while the remote was up left a process running with nothing on screen to
reach it by. shut() now destroys the others first and the main window last.

### The .exe that could never have worked

`MPV_GUESSES` began with `os.path.join(HERE, "mpv.exe")`, unconditionally.
`os.path.isfile` says yes to that on a Mac as readily as on Windows, so
`find_mpv()` returned a PE32+ binary and `subprocess.Popen` failed with
nothing readable on the way out. `find_ytdlp()` had it too.

The README has been claiming since v0.1.x that the .exe files "are ignored
on other systems". They were not ignored anywhere; nothing looked. **No Mac
could ever have played a file**, whatever else was installed first — which
is worth knowing, because every other Mac problem was downstream of this one
and none of them were the cause.

Both lists are now split on `os.name` before anything looks at the disk.

### What the port actually needed

Less than expected. The IPC half was already right — a unix socket in the
temp directory rather than a named pipe, and `proc.terminate()` rather than
`taskkill`, both already written and both correct. What was wrong was the
edges: drive detection, the browser fallback list, `pip install --user`
in run.sh (which modern Python refuses outright under PEP 668), and error
text telling Mac users a path should end in `mpv.exe`.

`restore_resizing()` returning early on non-Windows turned out to be right,
not a gap. pywebview's Cocoa backend *adds* to the style mask —
`frameless=True` ORs in `NSFullSizeContentViewWindowMask` and never clears
`NSResizableWindowMask` — so a frameless window keeps its resize edges for
free. The opposite of Win32, where dropping the frame drops WS_THICKFRAME
and the ctypes hack earns its keep.

### Drives, on a Mac

`/Volumes` instead of drive letters, with the exclusions worked out by
comparing `st_dev` rather than matching path prefixes — a prefix test would
be fooled by the firmlink that makes `/Volumes/Macintosh HD` look like a
separate disk when it is the boot volume.

One rule has no Windows equivalent: **a read-only mount is not offered.**
macOS mounts NTFS read-only, and an NTFS drive is precisely the drive
someone plugs into a Mac to move films around. Offering it would fail at the
first write with nothing to explain why.

### Bundled rather than installed

mac/ carries its own CPython and the official mpv build for Apple Silicon.
No Homebrew, no admin password, nothing outside the folder. mpv ships macOS
arm64 builds now, which is what makes this possible at all — and the bundle
includes libMoltenVK, so `vo=gpu-next` runs on Metal through Vulkan rather
than the deprecated OpenGL path everyone warns about.

mpv ships with hardware decoding OFF, which is the real substance behind
"mpv is bad on a Mac": untuned, it software-decodes 4K and the fans tell you
about it. mac/mpv_config/mpv.conf sets `hwdec=auto-safe`, and the app passes
`--config-dir` at both launch sites so the settings travel with the folder
instead of colonising `~/.config/mpv`. Verified rather than assumed:
`hwdec-current` reads back `videotoolbox` over the app's own control socket
on a 1080p HEVC 10-bit HDR file.

### A library that exists on a machine you are not sitting at

Asked for after the Mac scan came up empty, which is correct behaviour — a
library is keyed by file path, so a second machine genuinely starts with
nothing — and useless to look at. What travels now is the catalogue:
titles, years, TMDB ids, episode lists and your own ratings. Not the files.

**TMDB id is the key, never the path or the title.** The path is the thing
that differs between machines by definition. The title is worse than
useless: a title match would quietly hide a film you own behind one you
don't, and greying is only worth anything if it is right.

**It lives in its own tables.** `snapshot_movies`, `snapshot_shows`,
`snapshot_episodes`, and one row of `snapshot_meta` — not an `available`
column on the real ones. The scanner walks movies/episodes deciding what has
gone missing, and a row with no file is exactly what that logic exists to
clean up; see 2026-08-04, where an over-eager merge took out all twelve
BoJack episodes. Outside those tables an import cannot cause a deletion and
cannot be mistaken for something you own. It costs a `UNION`-shaped join in
`browse_library` and it is worth it.

**The role is derived, not configured.** A machine holding a snapshot of
somewhere else is the auxiliary one; a machine with no snapshot is just
itself. Nothing to set on either, and nothing to get wrong.

The import counts what was *stored*, not what arrived. tmdb_id is the
primary key, so two files of one film collapse into a single catalogue
entry — which is what you want on a shelf, but it made "125 imported" a lie
when 123 rows existed. It now reports the collapse instead. That is how the
duplicate copies of Parasite and The Big Lebowski surfaced: a 1080p and a
4K of each, both legitimate, both in MOVIES/.

Greyed tiles are desaturated rather than merely dimmed — across a wall of
posters colour reads faster than brightness, and a dimmed poster just looks
like bad artwork. They carry a badge naming the machine that has it, the
hover panel says the same in words, and the click is inert: no detail page,
no watchlist, no favourite, nothing that posts to an endpoint keyed by a
local id it hasn't got.

Rough edges, deliberately left: ratings made on the auxiliary machine do not
travel home — the snapshot is one-way. Nothing reconciles two snapshots.
And a snapshot is a moment, so it drifts until the next export.

---

## 2026-09-13 — v0.1.20

### A tick or a cross on every poster

Asked for, as a better way to do migration: press SELECT and every poster
says whether it's on the chosen drive — a blue tick or a red cross, the same
size as the green rating, gone again when you're done. The v0.1.17 design
only badged the posters that *were* on the drive, as a teal pill, which left
a missing pill meaning either "no" or "didn't look". Now every poster gets
an answer.

The mark sits flush in the poster's top-left corner and mirrors the rating
in the top-right exactly — same face, 10.5px bold, 3px 7px padding, 22px
tall, measured against each other rather than eyeballed — so the pair read
as *what you think of it* and *whether it's already there*. Blue tick on the
drive, red cross not, and an amber count such as **78/171** for a show only
partly across, because partial is neither of the other two. The watchlist
bookmark that normally lives in that corner steps aside while selecting.
Leaving SELECT invalidates any drive check still in flight, so a slow answer
can't paint marks back onto a grid that's finished selecting.

**The new design exposed an old wrong answer.** Before trusting the marks,
they were compared with the Drives view from v0.1.19 — and disagreed on
every show and 41 films. The SELECT check only recognised a file under the
library's own exact filename, `Aladdin (1992).mkv`; the drive's hand-copied
files are named their own way. The v0.1.17 pill had exactly this flaw and
failed silently, by showing nothing. A red cross would have turned it into a
false statement on Aladdin, Midsommar, Mulan and every episode of Seinfeld.

So the marks, the price and the copy now share **one answer**, and it's the
Drives view's. The catalogue records which library film or *episode* each
file on the drive was matched to — by filename, folded filename, parsed
title, or a stray's episode number ("921 & 922" is S09E21) — and a planned
file counts as on the drive if its library id was matched or its name sits
there already. After: 124 films in both views with no disagreement, shows
marked honestly (Arrested Development ✓, Seinfeld 78/171, The Simpsons
66/139 where one file maps to no known episode and is counted
conservatively), in 0.05s across the whole library.

**A tick is now a promise.** Priced read-only against the real drive,
Aladdin — which has no identically named file on G: — was ticked *and*
skipped; 12 Angry Men was crossed and copied; Seinfeld skipped exactly its
78 episodes on the drive, finale included, and priced the other 93. The
copy worker applies the same test, so nothing ticked is ever copied twice.
The trade to know about: a drive's copy that matched by title is trusted
even if it's a different encode of the film, which is what a tick has to
mean for "already have it" to hold.

**And a disabled primary button now looks disabled.** ADD TO DRIVE with
nothing ticked was correctly disabled but still the brightest thing on
screen, with a pointer. The facelift never styled `.play:disabled`; now it
fades and goes flat, everywhere a Play button can be disabled.

---

## 2026-09-13 — v0.1.19

### A drive, shown like the Library

Asked for: a mini version of the Library for external drives, just to see
what's on one. It's a sixth section of the Library view, **Drives**, on the
same footing as History and Recommendations: pick a plugged-in drive and get
the poster grid, films then shows, with the drive's totals above — *121
films · 16 shows, 487 episodes · 868 GB of video · 942 GB free* for G:. Search,
films-or-TV, and a switch for **only what isn't in my library** — the useful
question when a drive comes back from somewhere else.

Read-only, and cheap. It reads the drive through the same single walk the
copy tray uses and shares its cache, so G: comes back in 0.2 seconds, and it
never touches the media drive: every match is made from names. A title the
library also has wears its poster and opens its own page. A title it doesn't
is shown by the name on the file, badged **NOT IN LIBRARY**, and opens
nothing, because there is nothing to open. A show says how much of the
library's run is on the drive — *Seinfeld: 78 of 171 eps*.

**The matching was the work.** A first pass matched 116 of G:'s 124 films
and 15 of 16 shows. Every miss had a different cause, and each got its own
fix rather than one loose rule that would have caught them all and much else
besides:

- **Cowboy Bebop: The Movie** was in the library under a filename differing
  by one character — a Windows-safe rename swaps ":" for the lookalike "꞉".
  Filenames are now also compared with punctuation and extension folded,
  but only when exactly one library file folds to that name; "s01e01" names
  a hundred things and is never used.
- **Ex Machina** is 2014 on the folder and 2015 on TMDB. A title now matches
  on its year or one either side. Four out is a remake, not a match.
- **Dr Strangelove** and **Star Wars – Episode VI – Return of the Jedi** are
  short and long forms of the library's titles. A contained title matches,
  but only on the exact year, only when it names one film, and only when the
  shorter of the two names is at least ten letters — checking the first
  version of that rule against a fixture showed a film called just *Return*
  from 1983 would have been taken for the Jedi.
- **Love Death and Robots** is "Love, Death & Robots" to TMDB. "&" now reads
  as "and".
- **Seinfeld's "921 & 922 – The Clip Show"** and **Star Trek's "S01E01E02"**
  are double episodes the parser doesn't place, so they read as films. A
  file that still reads as a film but sits in a show's own folder, with an
  episode number in its parsed name, now belongs to that show. The parsed
  name, not the raw filename, so "1080p" never counts as one.

After: all 121 films and all 16 shows on G: matched, and every guard was
proven against a fixture built to trip it — the remake year, the short
prefix, a resolution in a show folder, a sample under 50 MB — before and
after the tightening, with the fixture removed afterwards. The main library
turned out not to be misfiling the Seinfeld finale; only the drive's copies
are named that way.

**One latent bug fixed on the way.** The copy tray belongs to the shelf, but
nothing hid it when you switched to a panel, so ticking things and then
opening History or Recommendations left the tray hanging under a view that
had nothing to do with it. Every panel now hides it.

---

## 2026-09-13 — v0.1.18

### "It's already on there" — but not where the app looked

Reported within the hour: the app offered to copy Akira to G:, and Akira was
already on G:. The guess that came with the report — "maybe because it's not
in the root?" — was exactly right. The v0.1.17 check looked at one path, the
one the app itself would write to: `G:\Films\Akira (1988)\Akira (1988).mkv`.
The file sits at `G:\MOVIES\Akira (1988)\Akira (1988).mkv`, same name, same
5.62 GB, put there by hand under the drive's own layout. A copy the app
didn't make was invisible to it.

**The drive gets read, once.** `dock_drive_index` walks the whole drive for
video files and keeps `{name: {size: path}}` — 1,068 names on G: in 1.2
seconds, then answered from memory for two minutes, and forgotten the moment
a copy to that drive finishes so the files it just wrote are seen next time.
The walk has a budget, and a drive too big to finish inside it is indexed
as far as it got and says so on the tray, rather than hanging the page.

A file's name and size together are identity enough. The two Kurosawa
featurettes with "Akira" in their names matched nothing, and a same-name
file at a different size is offered for copying rather than mistaken for a
twin. The posters use the looser test (name anywhere on the drive) because
that is a glance across a page; the price step and the copy worker use the
exact one, and now skip a twin wherever it sits rather than only at the
planned path — so nothing ends up on the drive twice under two folders. The
poster's tooltip says where it found the copy, which is the whole point
when that isn't where the app would have put it.

**And a path bug that had been working by luck.** The drive picker hands
over a bare `G:`, and `os.path.join("G:", "MOVIES")` is `G:MOVIES` — a
drive-relative path, resolved against whatever G:'s current directory
happens to be. It has been the root every time, so every copy since
v0.1.12 landed correctly, but the paths it produced were wrong to look at
and would have gone wrong the first time anything changed directory on that
drive. `dock_root` turns a bare letter into a real root before anything
joins onto it.

Verified against the real drive, read-only: Akira and Seven Samurai found
under `MOVIES\`, 12 Angry Men correctly absent, the price step skipping the
two and quoting only the third, and on screen Akira, Rashomon and Seven
Samurai all marked ON DRIVE with the tray declining to copy. No copy was
run.

---

## 2026-09-13 — v0.1.17

### The drop-downs were white

Reported the moment the facelift shipped, and it was the facelift's fault.
Every `<select>` got the tonal input treatment — a translucent white fill on
the dark room — which looked right closed. But the opened list is drawn by
the browser, not the page, and Chromium will only carry an OPAQUE background
across from the control into that list. Translucent, it fell back to white,
and put our cream text on it.

Two lines: the options get their own solid colours, and `color-scheme:dark`
on the control tells it to draw its native parts dark in the first place.
Worth remembering as a rule — anything the browser draws for itself
(popups, scrollbars, date pickers) wants an opaque colour and a
`color-scheme`, whatever the page around it is doing.

### "Is that already on the drive?"

Asked for while ticking things to copy, and the answer belongs in two
places. The copy worker already skipped a destination file that existed at
the same size — so re-running a job was always safe — but nothing said so
until the job was running.

**On the posters.** Once a drive is chosen in the tray, each poster on
screen carries a teal **ON DRIVE** pill if every file it means is already
there, or an amber **2/11 ON DRIVE** if only some are, and the art dims a
touch. Asked of the drive itself, one request per page, re-asked when the
drive changes — the drive is the truth, and it may have been filled by
another machine since anything here was written down. A file counts as
there if something sits at its planned path with a size above zero, which
answers from the destination alone and never wakes the media drive to
answer a question about a different one. A copy that stopped partway leaves
a `.nextup-part` beside the real name and nothing at it, so it reads
correctly as not there.

**In the price.** The plan applies the copy worker's own exact test — same
path, same size — and prices only what will actually move: *11 files to
copy, 2.75 GB. 1 already on the drive (3.09 GB), skipped.* The confirm
button quotes the remaining size. Tick a set that's entirely there and it
says so in green rather than offering to copy nothing.

The two tests differ on purpose. "Something at the path" is a glance across
a hundred posters; "same size" is the exact answer for the files you are
about to commit to. On a real drive the two agree, because a finished copy
is the same size as its source.

Tested against a fixture folder standing in for a drive — the film placed
in full at its exact size, the show with two of eleven episodes — so no
real drive was written to. The tray, the badges and the price all agreed
with a direct call of `dock_presence`.

---

## 2026-09-13 — v0.1.16

### Tick posters, add them to a drive

Asked for: select a list of things and send them to a drive. The docking
station from v0.1.12 already did the sending, from a checklist in Settings
— which is the right engine and the wrong front door. Nobody browsing the
library wants to go to Settings, search for the same titles again and tick
them in a second list.

So the Library has a **SELECT** mode. Press it and posters become things you
tick rather than things you open: a hollow ring in each poster's corner, a
marigold disc when ticked, a marigold ring round the tile. A tray appears
under the grid with a drive picker and **ADD TO DRIVE**. Escape or DONE
leaves the mode; the ticks stay.

**One selection, not two.** The tray writes into the docking station's own
Map, so a film ticked in the Library is ticked in the Settings checklist
and vice versa, and a copy started from either place is one job — the
tray polls it, and Settings adopts it if opened mid-way. The drive pickers
follow each other. Nothing on the server changed: `/api/dock/plan`,
`/api/dock/start` and `/api/dock/status` were already the whole contract.

Two presses to start, on purpose. The first prices the job — files, size,
whether it fits — because the size can't be known until every source file
has been stat'd, and it's the number worth seeing before a multi-gigabyte
copy begins. The button then says exactly what the second press commits
to: *CONFIRM — COPY 9.27 GB*.

**Tested against real drives, up to but not including the copy.** Three
ticked across two shelves priced at 13 files, 9.27 GB against HDD 2; the
selection survived switching shelves and pages, showed as "3 selected" in
Settings, and Escape handed the posters back to opening things. The running
and finished states were exercised with a stubbed status, not a real copy —
starting one writes gigabytes to a drive and isn't something to do in
passing.

The hover peek is off while selecting. It's an overlay over the poster with
its own live buttons, and it was the wrong thing to read when the question
on screen is "which of these do I want".

---

## 2026-09-13 — v0.1.15

### The facelift

Asked for: less wire-frame, more like a fully funded app. A fair verdict —
the screenshot before this pass was a page of thin-bordered rectangles with
a small poster tucked into the corner of each, and the one piece of imagery
that could carry a screen was never drawn at all.

Three decisions, and every edit belongs to one of them.

**The picture goes behind the words.** Every film and show has had a wide
backdrop on record since v0.1.1 — 537 of 538 films, 70 of 75 shows, with a
remote fallback when the copy isn't on disk — and the detail sheets were
even *sent* it in their payload, then never used it. The Now pick and both
detail sheets now draw it full-bleed behind the panel, masked so it is
strongest along the top band behind the title and gone by the time the body
copy starts, with the poster floating over it on a shadow. This is the
single change that moves the app from a list to a thing, and the data was
sitting there.

The mask direction was decided by the worst case, not the first one. The
film sheet looked right immediately because *10,000 BC* has a dark frame;
the show sheet put grey copy over a pale, busy anime still and lost it.
Words sit centre-right, over the brightest part of most frames, so the fade
runs top-to-bottom as much as left-to-right, and copy that shares a panel
with a picture carries a halo and steps up a shade from muted.

**Elevation instead of outlines.** A `1px solid var(--line)` around every
card, panel and button is the whole of the wire-frame feel. They are all
gone — the border is kept but made transparent, so nothing shifts by a
pixel — and each surface is instead a shade lighter than the room, lit by a
1px highlight along its top edge, and sat on a shadow. That is how a real
object reads, and what the border was a stand-in for. Hover lifts by shadow
and a faint edge, never by a grey line. The rulers between rows and under
headings stay, at a twentieth of the strength.

**One system for corners, buttons and inputs.** Cards 12px, panels 16px,
primary actions as pills — cream for Play, marigold gradient for Pick
something — and every secondary as a tonal fill rather than an outlined
box. Inputs are tonal with a marigold focus ring. Progress bars are lit,
with a soft glow, rather than painted. The tab bar is a segmented control
on a tonal track: the underline read as a document with headings, a lit
segment reads as a switch. Each channel card carries its own hue as a
faint wash at rest, so twenty-one of them stop being one grey wall.

**Where it lives.** One block, `THE FACELIFT`, at the end of the stylesheet,
which re-skins the component rules above it by coming later at the same
specificity. Kept together so the whole look can be read — or reverted —
as one decision rather than as forty edits that each made sense alone. The
only structural changes outside it are the design tokens, the tab bar, and
the three DOM hooks that attach a hero.

**Two things that bit on the way.**

- Lifting every non-hero child to `position:relative` so it sits above the
  picture caught the CLOSE button, which is absolutely placed in the corner
  and must stay so. Made relative it became a grid item, took the poster's
  column, and shoved the whole sheet one cell to the right. Excluded by
  name.
- The focus-ring rule set `border-radius:2px` on any focused button, which
  had been squaring every rounded control for a frame each time it took
  focus. Nobody had noticed because nothing was rounded enough to show it.

The remote is untouched. It sits on top of a film and was already black
for that reason; none of this belonged there.

---

## 2026-09-08 — v0.1.14

### The Rate screen became a place you can leave from

Both lists on it were dead ends. The card in the queue showed a poster, a
plot and a score control, and there was no way to open the thing or put it
on — the only route to a film you'd just been asked about was to leave the
tab and find it again in the library. The top tens were worse: ten films and
ten shows you have personally rated highest, and the only interactive thing
on any row was the score.

Both now go through the same two functions, so the queue and the lists
behave identically:

- **`openRated`** — a film opens its page, a show opens its own. The poster
  and the title on the rate card do it, and so does any row of the top tens.
- **`ratedPlayButton`** — a film plays itself; a show plays the episode you
  are up to. Which episode that is comes from the server as `play_id`, using
  the same `series_progress` reckoning the Now tab uses, so a show offers the
  same episode wherever in the app you meet it. The button says so: **PLAY
  S09E15** on Seinfeld, **PLAY S01E01** on something never started.

`resume: true` on everything here, which is safe rather than lucky —
finishing something zeroes its stored position, so it starts at the
beginning unless there genuinely is a place to pick up from.

**Films in the queue had no play target at first.** Shows got `play_id` and
films didn't, and because the button disables itself when there's nothing to
play, it sat there looking deliberate and did nothing when pressed. Caught
by testing the payload rather than the appearance: a disabled button and a
broken one look identical from outside.

Two smaller things the change forced:

- The score button and the play button both `stopPropagation`, or pressing
  either would also open the sheet behind it. Editing a score in place also
  takes the row's own click handler off, since a rating control is nine
  half-stars and every one of them would otherwise open the page too.
- **The play buttons on the top tens are visible at rest.** They were hidden
  until hover, which reads better with twenty rows on screen — but an
  `opacity: 0` button is still in the tab order, so a keyboard would land on
  a control nobody could see. `:focus` only fixes that while the document
  itself has focus, which isn't a thing to rely on. They sit at half opacity
  and brighten under the pointer, which is what the show sheet already does
  with a PLAY on every episode row.

Worth knowing, not changed: **`episodeRow` in the show sheet still plays
without `resume`**, so an episode listed as "43% in" restarts from the
beginning if you press PLAY there. Same class as the bug fixed in v0.1.3,
left alone because it's a different screen from the one this session was
about.

---

## 2026-09-08 — v0.1.13

### Saturday Morning was showing Chappelle's Show

Asked whether Chappelle's Show turned up in the listings. It did: Everything
#1, Comedy #5, and **Saturday Morning #7**, twenty-eight blocks each. The
third one is the bug, and it was never really about Chappelle.

The channel's genres were `Animation, Family, Kids, Adventure, Comedy`, and
"Comedy" is a tag Seinfeld, Peep Show, It's Always Sunny, Nathan for You and
The Eric Andre Show all carry. Its four largest contributors were **Seinfeld
(171 blocks), South Park (169), It's Always Sunny (151) and The Simpsons
(139)** — ahead of Pokémon and SpongeBob. It was an adult comedy channel
wearing a children's name.

**No tightening of the genre rule would have fixed it**, which is worth
recording because it was the obvious first move. Dropping Comedy clears the
live-action comedy but leaves Invincible, Love Death & Robots and Attack on
Titan, all tagged plain Animation. Requiring Family or Kids fails twice
over: `require_genres` is an AND across everything in it, so it can't say
"either", and in any case **exactly one show in the library carries either
tag** (SpongeBob). And TMDB tags Pokémon and Attack on Titan *identically* —
Animation, Action & Adventure, Sci-Fi & Fantasy — so no rule reading genres
can separate them.

So it goes the way All Day Daytime went: named by hand, with a new
`named_only` flag that makes the list the whole channel rather than an
addition to a genre rule. Also `tv_only`, since this is a morning schedule
and animated films already have Animated Features #19 — and nothing is left
homeless, because adult cartoons have Cartoon Swim #21 and anime has Anime
#11. It now carries Pokémon, SpongeBob and X-Men '97, 84 paired blocks, with
about eighty more titles listed against the day they arrive.

`_daytime_key` folds accents now. TMDB spells it "Pokémon" and a list typed
by hand says "Pokemon"; without folding those are different programmes and
the entry silently matches nothing — the exact failure this normaliser
exists to prevent, in the one channel that most needed it.

### Everything else in the listings, checked

All 21 resolve, none empty, no errors. Universal #2's fifty films are all
genuinely family. The two thin ones are thin by design — Directors Cut #9
shows one director at a time (Tarantino today) and In Black & White #18 is
the ten black-and-white films that exist here.

Three small things, none worth changing on their own:

- **Anime #11 carries The Super Mario Bros. Movie**, on a country match
  against `Japan|United States of America`. World Cinema solved this class
  of problem by matching on the language a film was shot in rather than
  where it was produced.
- **Universal #2 has one TV show**, for the reason above: SpongeBob is the
  only thing in the library tagged Family or Kids. It's a family *film*
  channel in practice.
- **Comedy #5 carries The Bear and The White Lotus**, both of which TMDB
  files as comedies. Nothing wrong with the channel; TMDB's tag is doing
  what TMDB's tag does.

---

## 2026-08-24 — v0.1.12

### A docking station, for the laptop that isn't the one with the library

The library lives on the desktop, on a drive that spins down when it isn't
needed. That's fine until you want to take some of it somewhere else — a
laptop, a car, a TV with no network — and the only way to do that has been
to go and find the files yourself in Explorer. Settings gets a new section
that does the finding: plug a drive in, tick what you want, and Next Up
copies it across as `Films\` and `TV Shows\` folders, ready for another
player to point at without any renaming.

**One-way and additive on purpose.** It only ever reads from the library's
own drives and writes to whatever's plugged in — nothing here deletes or
moves the original, so the worst a mistake costs is running it again.
That's also why there's no confirmation dialog on the destructive-action
front: there's no destructive action. The one thing it does ask you to
confirm is the copy itself, once it knows the real size — "2 files, 6.53
GB" against the free space on the drive you picked — because that's the
number that can't be known until every source file has been stated, and
it's worth seeing before it starts.

**Drive detection excludes on purpose, not by luck.** The system drive,
every drive a media folder lives on, and the drive Next Up itself runs
from are all filtered out of the picker — offering the shelf you're
copying *from* as somewhere to put the copy is never right, and doing it
by exclusion rather than an allowlist means an actual USB HDD (which
Windows enumerates as `DRIVE_FIXED`, same as an internal disk, once it's
been formatted) still shows up.

**Copied in chunks, not in one `shutil.copy2` call.** A film on a USB hard
drive can take minutes to move, and a progress bar frozen for that whole
time is indistinguishable from a hang. 4MB at a time, with the running
total written to `DOCK["bytes_done"]` after every chunk, is what makes the
copying notice's progress bar move continuously instead of jumping from
file to file. The same loop is what makes cancel land within a chunk
rather than at the end of the current file: written to a `.nextup-part`
sibling and renamed into place only on success, so a cancelled or failed
copy never leaves something at the real name that looks finished but
isn't.

**Sized before it's copied, under the same stall guard playback uses.**
`media_file_check` already exists for exactly this — a stat against a
drive that's asleep or gone doesn't fail, it waits forever — so the sizing
pass gets the same 3-second deadline per file instead of hanging the whole
job on one title from a drive that isn't answering. An item that times out
is dropped with a warning rather than stopping everything behind it.

Whole shows only, not individual episodes — the app doesn't have a picker
finer than that anywhere else either, and a show's files all move
together into `TV Shows\<Show>\Season NN\`.

---

## 2026-08-17 — v0.1.11

### A watchlist button on the Now card

NOT THIS was only ever half a thought. "Not tonight" and "but don't let me
forget it" are the same moment, and the card could only say the first — it
dropped the pick and moved on, and the thing was gone until the draw
happened to land on it again. Saying the second half meant leaving the page,
finding the title in the Library, and marking it there.

The same control as the Rate tab's, down to the bookmark and the label,
because it's the same act. On an episode it marks the *show*: the watchlist
holds programmes, and watchlisting S03E07 on its own means nothing — the
tooltip says which, since the card is showing you an episode.

Three small things it needed.

**The flag has to come with the pick.** `build_tonight` already read
`watchlisted` for the scoring bonus but never put it in the pick it handed
back, so the button would have opened in the wrong state and flicked to the
right one after the first click. Checked against the real library by drawing
until a watchlisted film came up: 12 Angry Men, flag true.

**And it has to be written back onto the pick object.** The Now page keeps a
trail of picks so BACK can replay them, and it replays the objects
themselves — so a toggle that only changed the button would be undone by
stepping back a card and forward again.

**The button was built for somewhere else.** `.watchtoggle` was made for a
tile's hover face, where it sits alone at the top of a stack:
`align-self:flex-start`, a tighter box, smaller type. In a row beside Play
and NOT THIS that made it float and read as a different class of thing. It
gives up all three inside `.rowbtns` and now measures exactly what NOT THIS
measures — 30px, same top edge.

---

## 2026-08-17 — v0.1.10

### Eight hours of Empire of the Sun

The watch history shipped this morning measuring how long mpv was open on
something. Reported the same day: it showed eight hours of Empire of the
Sun, because falling asleep in front of a film leaves the player running all
night and the wall clock has no idea you left.

That's not a bug in the measurement, it's the wrong measurement. How long
the window was open is a fact about the window. How far through the film the
playhead got is a fact about the film, and it's the one that answers "what
did I watch". Every number on the page is runtime covered now: **2h 17m,
89% of it** where it used to say eight hours.

`seconds` still gets written to the table — it costs nothing and it was
genuinely observed — but nothing reads it any more.

Two things fell out of the change that are worth having.

**A percentage on every row.** Once the number is runtime rather than
elapsed, "89% of it" is available for free and is the more useful of the two
figures — it's what you'd actually want to know about an evening you don't
fully remember.

**And the old rows became countable.** A row marked `watched` was seen out
to the end; that's what WATCHED_FRACTION decided when it was written. So the
runtime covered *is* the runtime, and where mpv never recorded a length the
library's own runtime answers instead. The 147 rows that read "not timed"
yesterday now read properly and add up: **137 of 148 measurable, 147h 42m**.
The remaining 11 are rows whose item has since left the library, so there's
nothing left to ask how long it was — those still say "not measured", which
is true.

Coverage is capped at the runtime. A position past the end is a rounding
artefact or a runtime that disagrees with the file, and neither is grounds
for claiming you watched 104% of something.

The Now tab needed no change: `recently_watched()` was already reading
position against total, so it was measuring the right thing from the start.
Empire of the Sun at 89% is over the 60% line and won't be offered again for
a month, which is the intended answer even though some of that 89% was spent
asleep — the app can see the playhead, not the room.

---

## 2026-08-17 — v0.1.9

### The slot grid is gone. It solved the right problem the wrong way

v0.1.8, one version old, put a gap at the end of every programme so that
about one channel in five was always sitting on something about to start.
It did fix "there's nothing near the start to tune into" — the measurements
in that entry are real. It fixed it by turning a fifth of the page into
channels that weren't running.

Reported as: "I want the channels to be running, not waiting for me to hit
play — I want to feel like I'm jumping in at the right time." Which is the
whole idea, said better than the feature said it. A channel's entire claim
on you is that it's already going and you drop into the middle of it. A card
reading "IN 21M — WATCH FROM THE START" is a play button wearing a
schedule's clothes, and it is a worse thing to look at than a film you're
twenty minutes late for.

There is no version of this that keeps both. Blocks either run nose to tail,
in which case there is no dead time and no reliable supply of fresh starts,
or they don't. So: nose to tail. `channel_now` has one state again, every
card shows something running, and tuning in seeks you to where the schedule
says you are.

### SHUFFLE ALL does the job the gap was doing, without the waiting

The gap was answering a real question — "I've opened this page and there's
nothing I can start" — and dropping it would have handed that question back
unanswered. But there was already a button for exactly that moment, added in
the same version and for the same reason: *when there's nothing on you fancy*.

So the shuffle now deals a share of the page fresh. Two channels in five are
placed a couple of minutes into a programme at the instant you press it; the
rest land anywhere. Measured across five salts, that comes out at **9 to 12
of the 20 schedulable channels showing something less than ten minutes old,
three to six of them films** — higher than two in five because a channel of
half-hour episodes lands near a start on its own often enough.

The difference from the gap is the whole point: those channels are *running*.
A minute in, mid-scene, nothing waiting on you.

This needed the epoch to move. A phase is a constant and "now" isn't, so
saying "this channel is two minutes into something" is only true relative to
a moment — the moment you pressed the button. `channel_shuffled_at` is saved
alongside the salt and every loop is measured from it afterwards. The
freshness decays over the following ten minutes as those channels get
further in, which is exactly how long it needs to last: you press it because
you're looking for something to put on, and then you put something on.

Not all of them deliberately. A page where everything began ten seconds ago
has no choice on it — half of what makes twenty-one channels worth browsing
is that some are deep in something you'd want to catch the end of.

### Three channels were showing South Park at once

Reported, and exactly what the collision rule permitted. `_block_identity`
was the *episode block* — `("episodes", (1043, 1044, 1045))` — so Binge,
Comedy and Cartoon Swim could each hold a different run of South Park and
never once collide by that measure. Nobody scanning the page cares that the
episodes differ. It reads as the same programme three times.

The identity is now the show. Checked across a full day at three-minute
intervals: **0 moments with a repeated title, and not one channel left with
nothing to show** — the walk-forward in `channel_now` finds another block
every time, because the pools are deep enough to afford it.

### A watch history, and how long you sat there

Three new columns on `history`, because one number couldn't carry it and the
three answer different questions:

  - `seconds` — how long the player was open on it. Wall clock, so a pause to
    make tea counts. It's the honest reading of "for how long" and the only
    one that can actually be observed.
  - `position` — where in the file you got to.
  - `total` — how long the thing is by mpv's reckoning rather than TMDB's, so
    "got to 48m of 1h52m" is two facts from one source.

Both ends of a sitting are recorded now, not just the finished ones.
Stopping half way through is a thing you did with an evening, and a history
that only lists what you saw out to the end is missing most of them —
`_record_position` logs a `stopped` row beside the resume point it was
already writing.

The page is a Library sub-tab, on the same footing as Recommendations: still
your collection, this time by the evenings you spent on it. Grouped by day
(Today, Yesterday, then the date), newest first, with a range selector from
a week to everything.

Two things it refuses to do. Episodes are logged under the episode's own
title — "Lisa the Beauty Queen", with nothing to say it's The Simpsons —
which is unreadable in a list of a hundred evenings, so the show carries the
row and the episode goes underneath it. And the 147 rows already in this
history predate the columns, so they have no length at all: those read "—
not timed" rather than "0m", and the total says "147 sittings, lengths
recorded from now on" rather than claiming three months of television took
zero minutes. A watch history that quietly rounds up is worse than a short
one.

### The Now tab reads it

Asked for directly: don't suggest films watched more than 60% of in the last
month. `recently_watched()` reads the history — not `resume_pos`, which is a
current state and gets cleared the moment something finishes, so it can say
"you're 40 minutes into this" but never "you finished this a fortnight ago".
The history is the only thing that remembers.

Sixty per cent rather than the 97% that counts as finished, because walking
out of a film with half an hour left is still having watched it. Thirty days
because that's long enough not to come round again the same month and short
enough that a favourite is offerable again by next season.

It goes into `exclude` inside `build_tonight` rather than being passed in,
which puts it beyond the reach of `picks_with_cooldown` — the offer cooldown
is given up by halves when the filters are tight, and this shouldn't be. "I
watched that last week" doesn't stop being true because Documentary under
100 minutes only matches three things.

Against the real library: 141 items currently in the quarantine, and across
**75 draws (54 distinct titles) not one landed on any of them.**

Timestamps compare as strings, deliberately. `now_stamp()` writes a
fixed-width `%Y-%m-%d %H:%M:%S`, which orders identically to the dates it
represents, so the last-thirty-days cut happens in SQLite instead of over
every row ever written.

---

## 2026-08-17 — v0.1.8

> The slot grid described below was walked back the same day in v0.1.9 —
> see above for why. The three new channels, SHUFFLE ALL, the For you year
> range and the Recommendations spacing all stayed.

### Channels run on a slot grid now, so there's always something about to start

Reported as: "sometimes I go onto the Channels page and there isn't anything
near enough to the start to tune in to, especially if it's a film." That is
exactly what the old schedule guaranteed. Blocks ran nose to tail, so each
channel sat at a uniformly random point inside whatever was on, and for a
two-hour film the odds of being less than ten minutes in are one in twelve.

Measured against the real library, sampling every three minutes across a
whole day: **on 99 of 480 samples — a fifth of the day — not one of the
twenty-one channels had a film you could join near its start.** Which means
the complaint wasn't "sometimes", it was "most evenings, for stretches at a
time". Counting television as well it was better, 11 samples in 480 with
nothing at all, but television is not what you plan an evening around.

So programmes start on the half hour now, the way they do on actual
television. A block occupies however many whole thirty-minute slots it needs
plus at least ten minutes spare, and that spare end at the top of the slot —
where a real channel runs trailers and a continuity announcer — is the whole
mechanism. A channel sitting in it advertises the programme it's *about to
show* rather than the one you've missed half of, and tuning into one of those
starts it from the beginning a few minutes early.

Same measurement afterwards: **3 samples in 480 with no film near its start,
and never once a moment with nothing at all.** The median went from one film
to three, and from three channels to eight.

Two constants earned their values rather than being picked:

**The ten-minute minimum gap** (`CHANNEL_MIN_GAP`). Rounding to slot
boundaries alone leaves a film whose runtime lands just under a boundary with
a gap of seconds, and long runtimes make near-exact fits likeliest on exactly
the channels that most need a gap. Without the floor: 46 bad samples in 480.
With it: 3. A fifteen-minute floor was no better (8) and wasted more of the
schedule; padding by a whole extra slot got to zero but gave up 37% of the
schedule to do it, against 28%.

**The even stagger** (`_stagger_slot`). Every channel's boundaries land on the
same half hours, so without something to separate them all twenty-one start
together and nothing begins in between. The obvious fix is a random phase per
channel. The obvious fix is worse: measured across four salts it leaves 10 to
29 bad samples where an even spread leaves 3. Evenly spread channels *cannot*
all be mid-film at once; independently random ones can, and regularly are.

None of this costs anything while you're actually watching. A programme
ending hands straight over to the next one without waiting for the half hour
— the gap exists only in the listing, which is the one place it's useful.

The cards say which state they're in: a marigold `IN 12M` where something is
about to start, a teal `JUST ON` where it began in the last ten minutes, and
nothing at all otherwise. It's the same fact the line under the poster
already gives, repeated where the eye lands first, because the point of a
page of twenty-one cards is being able to scan it and "12m in" versus "starts
in 6m" is too fine a distinction to catch four rows down.

### SHUFFLE ALL

Everything about a channel is a pure function of your library and the clock.
That's what lets "what's on" be a fact rather than a state — no scheduler
thread, nothing to keep in sync, the same answer after a restart as before
one. The price is that a line-up you're bored of stays that way forever, and
a pile of files dropped on the drive this morning gets slotted into an order
settled long before they arrived. Both of those are the reasons given for
wanting the button, and they're the same reason.

One saved string, `channel_salt`, feeds every shuffle seed and every
channel's position in its own loop. Pressing the button rewrites it, so all
twenty-one channels get a new running order *and* a new place inside it, and
the result is still a pure function — just of a different constant than it
was a minute ago.

Landing everything at zero would have been the easy version and a bad one:
twenty-one films all one minute in is no more use than twenty-one all an hour
in, and it throws away a page you can browse. So the salt also throws each
channel a random number of slots into its own loop, and which of the evenly
spread stagger positions it holds. Measured across five different salts the
guarantee holds every time — never fewer than three channels near a start,
median eight.

Two channels can't be shuffled and are moved a different way instead.
Directors Cut plays one career in the order it happened, so shuffling it
would be shuffling the thing that makes it worth having; the salt shifts
which day of the rotation today counts as, and hands the channel to somebody
else. Al Jazeera Live is a pipe to a live stream and has no line-up at all.

### Three new channels

**Animated Features #19** — animation as a form rather than as a children's
shelf. Universal and Saturday Morning both put family first and both mix in
television; this is the 56 animated films on their own, Grave of the Fireflies
next to Shrek, which is the point.

**Top Shelf #20** — the mirror of Cult Classic: the same TMDB number read the
other way round, wanting the crowd rather than distrusting it. 8.0 is the
line because it's where the count stops being a handful and starts being a
channel — 102 films here clear it. The vote floor of 200 is the only guard,
against TMDB reporting 8.7 off thirty votes; every film currently over the
line has thousands, so it costs nothing today and stops an obscurity walking
in tomorrow.

**Cartoon Swim #21** — the late slot. This one needed two new keys on the
genre matcher. `require_genres` is an AND where `genres` has always been an
OR: Cartoon Swim means animated *and* funny, and either half alone is a
different channel entirely (Animation alone is Arcane and Grave of the
Fireflies; Comedy alone is every sitcom you own). `exclude_countries` keeps
the anime out — One-Punch Man is better served by Anime #11, and the cost of
losing the anime Adult Swim genuinely aired is the right way round when the
alternative is this channel slowly turning into Anime #11.

And a hand-kept title list beside the genre rule, for the same reason All Day
Daytime has one and one more: the block this channel means isn't all
animated. The Eric Andre Show, Tim and Eric and Dr Steve Brule are live
action and tagged nothing but Comedy, so no genre rule reaches them and any
rule that did would drag in every sitcom. 132 blocks in the library today.

### For you got a year range

Two ordinary sliders lying on top of each other rather than one control with
two handles, because there is no such input, and faking one with a div and
mouse arithmetic gives up the keyboard. The inputs are transparent and only
their thumbs answer the pointer, so the handle you reach for is the handle
you get; the rail and the lit stretch between them are drawn underneath.

The ends are the years the list actually covers, not a fixed 1900-to-now:
dragging across four empty decades to reach the first film anyone made is not
a control, it's a corridor. The bounds are held as null rather than as years,
so a library that gains a 1948 film widens the slider instead of hiding it.
Years and the lit stretch update live while you drag; the grid waits for you
to let go, because rebuilding a hundred cards on every pixel of a drag is how
a slider comes to feel stuck. Something TMDB has no year for isn't hidden by
a year filter — you can't place it either way, the same call the score slider
already makes.

The section count reads "20 OF 45" while a filter is on, so the number never
quietly disagrees with what's under it.

### And a touch of air

Browsing opens on a search row, which carries its own breathing space.
Recommendations opened straight onto the hub cards, hard against the sub-nav.
14px.

---

## 2026-08-16 — v0.1.7

### The shortlist was the watchlist, read out

Reported again after v0.1.4: still the same handful, still no surprises,
"there's 12 Angry Men again, there's Fantastic Four again". The cooldown
added in v0.1.4 was real but it was treating a symptom — and the v0.1.4 note
in this file said widening the pool was "real but modest… so it's left
alone", which was the wrong call on the wrong evidence. This is what was
actually happening.

**The watchlist bonus was a sort order, not a nudge.** It added 2.5 to a raw
TMDB rating, and the unrated half of this library spans 5.7 to 8.6 — a range
of 2.8. A bonus nearly as wide as the whole scale means every watchlisted
film outranks every other one no matter how good. There are **15 unrated
watchlisted films and 16 unrated film slots in the draw pool**, so the film
half of "pick something" was the watchlist read out in order, with one seat
spare. That's the whole mystery: The Fantastic 4 at TMDB 7.0 held a
permanent place ahead of two hundred better films for no reason except that
it had been ticked. Now `WATCHLIST_BONUS`, at 0.6 — it lifts a film over
others of about its standing and loses to one that's genuinely better.

**The pool was 40 titles out of 587.** `40 // len(by_type)` gave twenty
films and twenty episodes, so 93% of what passed the filters could never be
drawn at all, and the cooldown only slid that little window down the
ranking. Now `POOL_PER_TYPE = 60` each.

**Nothing was ever chosen at random.** Everything in here is a machine for
finding the *best* thing, and a machine like that answers the same way every
time you ask it — the ranking of a library that isn't changing doesn't
change either. `WILDCARD_SHARE`, one draw in four, takes anything at all
from what's eligible, uniform and unranked. Weighting it would only have
made it another ranking. It draws from what has already passed every filter
and the cooldown, so the worst it can offer is something you own, haven't
disliked, and asked to see.

**And fifty was too shallow a memory.** It guaranteed no repeat inside fifty
draws and delivered precisely that — the favourites returned on the
fifty-first, forever, which is what "again" meant. Now 150.

Measured over 200 draws against the real library, all four changes
together: **93 distinct titles became 183**, the closest repeat went from 51
draws apart to 151, and the watchlist went from 32% of all picks to 14% —
still well represented, no longer the whole list. In a 25-press sample, **22
were titles the old settings could not have produced**: Apocalypse Now, In
Bruges, Lawrence of Arabia, Tokyo Story, Chinatown, Once Upon a Time in the
West.

**The deep memory needed a gentler failure.** Some filter combinations leave
very little standing — Horror under 90 minutes matches nothing here,
Documentary under 100 matches three — and holding back 150 would empty them.
`picks_with_cooldown` gives the memory up by halves instead of all at once,
so each shelf gets the deepest one it can carry: TV, with 63 eligible, used
all 63 across 100 draws; the three-film Documentary shelf cycles its three;
the impossible one still says so. Costs nothing in the ordinary case, which
returns on the first attempt in about 9ms.

---

## 2026-08-16 — v0.1.6

### The Now page stopped jumping when you press Pick something

Reported as a flicker where "Continue where you left off" fills the
suggestion area for a split second. It wasn't a repaint, it was a layout
collapse, and the numbers are worth writing down: pressing the button
emptied `#tonight-out` and wrote "Picking…" into it, taking the card from
**394px to 45px**, and cleared `#reasons-out`, taking it from **165px to
zero**. Everything below rose to fill the gap — "Continue where you left
off" travelled **551px up the page and back**, measured by sampling the
layout every 6ms across a press.

The draw itself takes about **fifteen milliseconds**. So this was one or
two frames of most of the window moving, on every press, on the one button
you press over and over.

The fix is to stop clearing anything before there's something to put in its
place. The outgoing pick stays exactly where it is and only its ink fades
(`.swapping`, and clicks off, since what's under the pointer is on its way
out), then the new card replaces it in a single operation. The reasons
panel can't stay — it belongs to a pick that's no longer shown — so it
keeps its *height* instead while its own lookup runs, and gives that back
once the new cards have a height of their own.

Measured after: **551px of travel became 21–46px**, and that residue isn't
flicker at all — it's one film having a longer plot or one more reason card
than the last, settling once in the honest direction. The card never drops
below its real height again. Held up under eight presses at 120ms intervals
— the "flicking through films" case — where the card never fell below 352px
and the whole run moved 67px in total.

No throttle was added. The endpoint answers in ~15ms, so presses can't
realistically pile up, and blocking them would have made the button feel
worse than the bug did.

---

## 2026-08-15 — v0.1.5

### Recommendations moved into the Library, and stopped forgetting

Three changes that turned out to be one: it was never a place of its own.
It's your collection you're looking at, just the part of it you don't own
yet — so it's a shelf of the Library now, fourth after Favourites, and the
top-level tab is gone.

**The forgetting was a one-line omission, not a missing feature.** The
results have been written to `nextup_recs.json` when a scan finishes and
read back at startup since v0.1.1 — `load_saved_recs()` runs in `main()`,
and the file on disk is 119KB of perfectly good answers. But `pollScan()`,
the only thing that ever sets `LAST_SCAN` in the page, was wired to the
scan button and nothing else. So the server knew and the page never asked:
every launch showed "Nothing scanned yet — press Find what's missing" over
a full set of saved results, and pressing it spent a few hundred TMDB
lookups rediscovering them. Opening the shelf now asks first, and only
shows the empty prompt when the answer really is empty.

Since a shelf can now arrive already full, it says when it was filled —
`age_days` was already in the payload and had never been shown. "Last
looked today", quietly, above the results.

Which half of the Library shows is a `showing-recs` class on the parent
driving CSS, not four `hidden` toggles in javascript. The pager already
owns its own `hidden` to say whether there's a second page, and two owners
of one class is how you get a pager that never comes back.

Two things that had to follow it across: the wheel handler, which hands a
scroll with nothing under it to whichever panel is actually scrolling —
that's `#tiles-out` when browsing and `#view-upnext` when not — and the Now
tab's "find something in this genre to download", which used to be a tab
switch and is now a tab and a section. Switching sections leaves the shelf,
kind and sort alone, so going back to Films finds it as you left it.

### Settings became a gear

The one tab that isn't somewhere you browse — it's a thing you go and
adjust. The label lives in `aria-label` and the tooltip, so nothing is lost
to a screen reader, and the icon is the same Feather set the library's
re-scan button already uses.

Worth noting what it bought beyond the look: six worded tabs no longer fit
on one row at the window's own 760px minimum. Five, with the last one 43px
wide, do.

---

## 2026-08-09 — v0.1.4

### The Now tab stopped offering the same six films

Reported as "it's the same ones over and over", and it was — by design,
without anyone meaning it. The draw was always random, but random from a
pool of forty with position weighting at `1/(i+3)`: the strongest item took
a sixth of every draw on its own. The only thing holding anything back was
the skip list, which lived in the page and lasted until you changed a
filter or closed the app.

So there is now a **persistent memory of what's been offered** — a table of
the last fifty picks, excluded from the next draw, surviving restarts. Only
the first pick counts as offered, because only the first is ever shown; the
other two the endpoint returns have never been rendered.

Measured over 180 simulated picks against the real library: the closest
repeat is **51 apart**, which is the guarantee working exactly, and 87
distinct titles came up where the old behaviour circled a handful. Twelve
consecutive calls with an empty skip list returned twelve different things.

Worth knowing before widening it: 587 titles pass the filters but the draw
pool is capped at 40, so the cooldown slides that window down the ranking
rather than opening the whole shelf. Raising the cap to 80 takes the 180-run
from 87 distinct to 97, and to 120 takes it to 109 — real but modest, and
paid for in the quality of what surfaces, so it's left alone. The number to
change is `OFFER_MEMORY`, or the `40` in `weighted_sample`.

> **Wrong, and corrected in v0.1.7.** Widening the pool looked modest here
> only because it was measured on its own, against a ranking that was
> broken underneath: the watchlist bonus was large enough to pin the same
> fifteen films to the top whatever the pool size. Fixing that, widening
> the pool, adding a genuine random share and deepening the memory together
> took the same measurement from 93 distinct to 183. The complaint was
> repeated after this entry was written, which is what prompted looking
> again.

Three constraints now, given up in the order that costs least: the cooldown
goes first, because a fresh list of nothing is no use; then this sitting's
skips; and only then is the screen allowed to come back empty. A tight
genre-and-mood combination therefore still answers.

### A way back to the one you skipped past

`‹ BACK` beside "Pick something", and deliberately the quieter of the two —
going back is the recovery, not the thing you came here to do. It's present
but disabled until there's something behind you, rather than appearing and
disappearing, which would move the button next to it.

The page keeps the picks themselves rather than their ids, so going back
costs no request and can't come back empty — which matters because the draw
is random, and "the one before" is something only the page still knows.

Three behaviours that had to be decided rather than fallen into:

- **A new draw truncates the forward branch.** Go back two, press Pick
  something, and the two you'd skipped past are gone — from there it's a
  different road, and keeping the old branch would make BACK lead somewhere
  you never went. Verified: branch at A, draw B, BACK returns to A.
- **A filter change wipes the trail.** Those picks answered a different
  question, and nothing on a card says which mood produced it.
- **The dead end keeps its trail.** When "nothing matches that" comes up,
  the trail is left alone and BACK is the way out — but it steps *onto* the
  trail rather than one further along it, or the last thing you actually
  saw would be skipped over. That's what the `offTrail` flag is for.

---

## 2026-08-09 — v0.1.3

### Continue where you left off, in the Library

A strip of up to four things across the top of the Library tab, above the
search row rather than inside the scrolling grid — the app opens on this
tab, so it answers "what was I watching" before you've asked anything, and
a thing you have to scroll to find is a thing you'd have searched for
instead.

Narrower than the Now tab's Continue list on purpose, and the two are
answering different questions. That one surveys everything outstanding,
including a series whose next episode you've never touched. This one is
four things to press, so it's **resume positions only, and only past five
minutes**. Below that you opened something, thought better of it, and
closed it again: 27 of the library's 122 stored positions are under five
minutes, and a shelf of those is a shelf of accidents.

Ordered newest first, by when the app last played the thing rather than by
how far in you are — the point of the row is the evening you interrupted,
which is a question about time, not progress. Anything with no recorded
play sorts to the end, because its position came from mpv's own
watch-later file and an unknown time is not a recent one. One entry per
show, never per episode.

**It had to be taught to actually resume.** `/api/play` always started at
zero, and for an episode it explicitly loads with `resume-playback=no` —
right for a channel, where the schedule decides where to come in, but it
meant a card reading "43% in" would have restarted from the beginning. The
endpoint now takes `resume: true` and seeks to the position the app itself
recorded, rather than leaving it to a watch-later file that only some of
the paths into the player consult. Two things that were already lying got
the same flag: the Now tab's Continue list, and the film sheet's button
that has always said **Resume**.

Two things the layout forced:

- The cards are four columns that shrink, never `auto-fit` that wrap. A
  second row doubles the strip's height and every one of those pixels
  comes out of the tile grid — at the window's own 760×600 minimum that
  left the grid **29px tall**.
- Even one row won't fit a short window, so below 700px of height the
  strip is gone entirely. The grid is what the Library tab is for.

It hides while you're searching, on the first keystroke rather than when
the results land — a search row that jumps 130px down a fifth of a second
later moves the grid out from under the pointer.

A card with no stored duration says "12 min in" and draws no bar, rather
than "0% in · 0 min left" over an empty track. mpv only writes a duration
back when it's asked for one, so a file played before this app started
watching positions has a real place in it and no idea how long it is —
Malcolm in the Middle S08E01 is exactly that case.

---

## 2026-08-08 — v0.1.2

### The lights went properly off

The main window joins the remote on true black — `#0b0a10` where `#17151c`
was, with the surfaces climbing back up through the old base colour as they
rise, so the plum warmth lives in the cards now rather than the walls.
Posters and marigold both sit better on it. A faint radial glow at the top
of the room keeps black from reading as a spreadsheet; the title strip and
masthead went transparent to sit on it, which they can because nothing ever
scrolls beneath either. The native window's own `background_color` moved to
match, or the first frame would flash the old colour.

### The fonts come off the shelf, not the wire

The faces were never basic — Bricolage Grotesque was just losing the race.
They loaded from Google on every launch, so every launch showed Segoe UI
for a beat before the real faces arrived, and with no connection the app
wore Segoe permanently — on a machine where everything else already works
offline. All three families are in `nextup_fonts/` now (273KB, the same
woff2 files Google serves), served by the app at `/fonts/` with the same
tight-name discipline as `/art/`. Zero requests leave the machine; the page
renders in its own faces from the first frame. A packaged build has to ship
the folder, same as the artwork.

### Polish

Elevation and motion, kept small. Tiles, cards and channel cards lift 2px
under the pointer with a soft shadow doing the rest; the detail sheet dims
*and blurs* what's behind it, so the library stays recognisably back there
instead of vanishing behind a curtain; sheet panels carry a real shadow and
a 10px radius, cards went 4 to 6. Buttons press down 1px when clicked, and
the marigold SPIN button now casts a marigold shadow. Selection is marigold
too. All of it sits behind the existing `prefers-reduced-motion` blanket.

### The stat got its deadline

The last Planned item, closed the way the note suggested. `os.path.exists`
against a drive that has spun down doesn't fail — it waits for as long as the
drive feels like, and the watchdog caught a channel change sitting six seconds
inside that one call. Every check of a media path now runs the stat on a
throwaway daemon thread and gives it three seconds (`media_file_check`),
chosen to stay under the watchdog's six so a slow drive reads as a message
rather than a stack dump. The abandoned thread finishes whenever the drive
gets round to it and costs nothing in the meantime.

One deliberate departure from the note, which said to reuse the missing-file
message: a drive that isn't answering does **not** get told "rescan your
folders". Pointed at a sleeping disk, that advice runs a scan against an
unreachable folder — the guards would hold, but the message would still be a
lie. It says the drive isn't answering, asleep or unplugged most likely, and
to try again in a moment.

Five call sites. Tuning a channel, the play button, stepping episodes, and
the subtitle fetch all go through `require_media_file`, which raises the
right complaint for each of the three answers. `continue_series` keeps its
own shape — end of the run, file gone, and drive not answering all close the
window, which is what it already did for two of the three.

---

## 2026-08-07

The show page in the Library — and then the hang, which is finally understood.

### The hang: found, and it was the remote all along

Reported as "opening the remote and adjusting the audio delay crashes the
app". It isn't a crash and it isn't the audio delay; the delay button is just
where you find out the window is already dead.

**Caught it live.** The process was still there, `Responding: False`, fourteen
threads and 1.9 seconds of CPU since launch — blocked, not spinning. `py-spy
dump --pid` reads a wedged process from outside without needing it to
cooperate, which is the tool this problem had been waiting for; faulthandler
can't help, because it needs the process to reach the code that calls it.

Three threads told the whole story:

    Thread-17 (generate_js_object)
        get_functions (webview\util.py:196)      <- getattr, four levels deep
        get_functions (webview\util.py:206)  x3
        generate_func (webview\util.py:214)
    Dummy-12
        on_web_resource_request (edgechromium.py:361)   <- on the GUI thread
    Thread-15 (process_request_thread)
        write (socketserver.py:845)
        send_file (nextup.py:5660)             <- blocked writing to WebView2

When a pywebview page loads, pywebview builds its javascript bridge by
walking the `js_api` object with `dir()` and `getattr()`, **recursing into
any attribute that is a plain object**. The remote handed its own window back
to the object serving as its `js_api`:

    controls.window = webview.create_window(..., js_api=controls)

So the walk stepped off `controls` into the pywebview `Window`, and from there
into `Window.gui` — the WinForms backend module, full of .NET types. Reading
those needs the GUI thread. The GUI thread was at that moment inside WebView2
setting up this very window. Each waited for the other, the window stopped
answering Windows' messages, and Windows killed it as an **AppHang**: no
traceback, because nothing was raised; no faulthandler dump, because nothing
faulted; no `closed` line, because the exit handler never ran.

It only bit sometimes because it is a race. The walk happens on page load; if
the page got there before the assignment, the attribute was still the class's
`None` and the walk stopped harmlessly.

**The fix is one underscore.** `controls._window` — pywebview skips names
beginning with one, so the Window is never entered. Confirmed by running
pywebview's own walk over both spellings: the public name enters the Window
and calls `getattr` on `width`, `height`, `x` and `y` — the four properties
that each do `events.shown.wait(15)` and then a synchronous `gui.get_size()`
on the GUI thread — while the underscored name enters nothing at all.

The rule worth keeping: **nothing hung off a js_api object may reference a
pywebview window, or anything leading into pywebview, under a public name.**
`WindowControls.big` went to `_big` for the same reason, though a bool was
never going to hurt anyone.

Note what this says about the watchdog: it was armed on channel changes only,
so it never covered this path and never fired for it. The thing that actually
cracked it was an external sampling profiler on a process that was still
hung. Worth reaching for first next time — and worth not closing the window,
because closing it is what lets Windows finish the process off.

### The PLAY button and the last cast tile hung off the edge

One fault, not two. `.sheetbody` is `grid-template-columns:180px 1fr`, and a
plain `1fr` is `minmax(auto, 1fr)` — the track is never allowed narrower than
its content's own minimum. An episode row is a flex row, so its minimum is the
sum of its parts' minimums, and one of those parts is a title set
`white-space:nowrap`. "$pringfield (Or, How I Learned to Stop Worrying and
Love Legalized Gambling)" has a minimum of 470px all by itself, which put the
row's minimum at 597 against a track of 564.

So the right-hand column was 33px wider than the panel's content box, and
everything flush to its right edge — the PLAY button on every row, the third
cast tile in every row of three — sat 8px out past the panel border. Measured
before and after rather than eyeballed: 1011.9px against a panel inner edge of
977.5px, now 976.5.

`minmax(0,1fr)` is the fix, on `.sheetbody` and on `.sheetpanel.main`, which
had the same latent bug on the film sheet. Worth knowing that `min-width:0` on
the title does **not** help: an element's min-content *contribution* to a flex
row isn't capped by its `min-width`, so the floor has to be lifted at the grid
track. Checked at the window's minimum size too (760px) — nothing overflows.

### A season at a time, opened where you left off

114 episodes stacked made a 5,744px sheet, so reaching season five meant
scrolling past four of them. Scrolling was being used as navigation, which is
what it's worst at. There's a bar of season tabs now and one season on screen:
1,719px.

- It opens on the season holding "next up", not on season one. On The Simpsons
  that's S04, where you're 91% through S04E12 — the reason you opened the page.
- Each tab carries a mark: a marigold dot for a season you're in the middle of,
  a teal tick for one you've finished. "In the middle of" is deliberately wider
  than `playcount` — being part way through an episode counts, and so does
  holding the next-up episode. `playcount` was never written before v0.1.1, so
  a season you're plainly mid-way through can have nothing marked in it.
- The bar is suppressed entirely for a single-season show. One button isn't a
  choice, and a bar of one reads as a bar missing its other buttons.
- The header line carries `progress_note` on the right — the API had been
  returning it since the page was built and nothing ever showed it.
- Specials sit at the end as `SPECIALS` rather than `S00`, and are never what
  the page opens on.

---

## 2026-08-06

A long session, most of it the remote — and one bug that ate a good deal of
it and is still open (see Planned, above).

### Type Cast rotates by the run, not by the day

A day is a length borrowed from the calendar and it fits nobody's
filmography. Thirteen actors qualify and their runs are 5.5 to 21.7 hours
long, so a daily rotation was wrong in both directions at once: Trey
Parker's four films played twice through and then got taken away
mid-Wednesday, while Brad Pitt's nine were cut off after the seventh and the
last two were never shown at all. The channel now holds a name for exactly
as long as their films last and moves on when they end.

The mechanism is smaller than the old one, not bigger. `channel_blocks` for
these types returns every qualifying name's films concatenated — thirteen
runs, sixty-nine films, about six days end to end — and the ordinary
schedule walk does the rest. Nobody has to work out whose turn it is: the
person on now is whoever the current block belongs to, which is written on
the block.

That also **deletes the special epoch**. The reason these two couldn't be
measured from 2024 like every other channel was that their line-up was
rebuilt at midnight, and measuring a new list against an old anchor drops
you in the middle of it. A run-rotating channel's list only changes when the
library does, so it goes back to the same fixed anchor as everything else
and the exception goes away.

Directors Cut is deliberately left on the daily rotation — `"rotate": "day"`
against Type Cast's `"rotate": "run"`, so switching it is one word. Worth
knowing before doing it: twenty-three directors and 314 hours means a full
cycle takes thirteen days, and Scorsese alone would hold the channel for
twenty-eight hours.

The card says which clock it's on. "Today: Paul Thomas Anderson" against
"This run: Clint Eastwood" — "today" would be a plain untruth on a channel
where a run can start at four in the afternoon and outlast midnight by
hours.

### The four things that were only planned

Cleared in a second pass, leaving the hang as the sole open item.

**The thumbnail survives the hover.** The poster comes back at 42px in the
top-right of the peek, ringed and shadowed so it doesn't sink into the tinted
panel. The peek reserves 66px of right padding for it, but only when there is
a poster — a channel whose art is missing keeps the full width for its text.
It sits last in the DOM: it's the same picture the heading already names, so
anything reading the card in order should reach the words first.

**"Trash TV" is now "All Day Daytime".** Genre couldn't carry it, exactly as
expected, so the channel is named by hand as well: a list of about fifty
programmes — motoring, workshop, auctions, kitchens, panel shows, daytime
sofas — matched on a normalised title, with the Reality/Talk/Soap genre match
kept alongside rather than replaced, so anything TMDB genuinely files that way
still lands here without being typed out first. Matching is deliberately
whole-title, not a prefix: a prefix would pick up regional spin-offs, and it
would also put a drama called "Survivors" on a channel that meant Survivor.
Most of the list isn't in the library yet, which is the point — it's there so
the channel picks these up on the day they arrive.

The immediate effect is smaller than the list suggests and larger than nothing:
73 blocks to 97, because Nathan for You was already on the shelf and Comedy /
Documentary was never going to find it. Top Gear and Mythbusters are still
waiting.

Named-by-hand beats every other rule in the channel, exclusions included —
putting a programme on the list *is* the decision about it. The mechanism is
general (`"titles": [...]` on any genre channel), not specific to this one.

**The audio delay reads `0ms`.** And in lower case: the label row uppercases
everything by default, which turned it into `0MS` directly above three buttons
that say `100ms`.

**The presets grid.** The floor was the fault, and not in the way it looked.
112px against three rows that actually measured 146px meant the grid had been
quietly scrolling all along, and every preset was losing the bottom few pixels
of its name — most of "skewed" was text cropped mid-descender. Three fixes:

- The buttons are one line instead of two, which is 12px a row and 44px
  overall — enough to bring six of them back inside the space there is. The
  floor is now written as `calc(3*32px + 2*7px)`, the arithmetic rather than a
  number nobody can check.
- The badge on the left is a fixed 30px, so every name in a column starts at
  the same x. Ragged left edges were the rest of what read as skew.
- An odd number left a hole where the last row's second column should be. The
  odd one out spans the full width now — a wide button reads as deliberate
  where a half-empty row reads as a mistake.

The badge also changed what it says. It was the preset's own ordinal, `P1`,
which the grid position already tells you; it now carries the channel number,
`#9`, which nothing else on the button does — and since names ellipsise from
the right, and the number moved to the end of every name this session, the
number was the first thing being eaten. Edit mode keeps `P1`, because there
the pick order is the whole point; the full name, number and all, is in the
tooltip on both.

### A refresh button in the Library
Re-scans your folders from the shelf you're standing at rather than from
Settings. Deliberately quiet: no border, no label, the same weight as the
title count beside it. It spells out `SCANNING 40%` as well as spinning,
because the animation is the first thing `prefers-reduced-motion` turns off
and a disabled button with no other signal looks broken. It reports `+12 −2`
or `UP TO DATE`, adopts a scan started from Settings if you switch tabs
mid-way, and says `BUSY` when a recommendations scan holds the worker —
that last one needed handling explicitly, or it would have reported the
*previous* scan's result as if it were this one's.

### Channel cards, made uniform
Eighteen cards at six different heights (164–224px) became eighteen at one.
`grid-auto-rows:1fr` alone would only have traded six sizes for one large
one, so the text had to stop varying first: titles and "up next" are held to
a single line with the full text a hover away, and the live and empty cards
lost their paragraphs to tooltips. "On now" is gone — the progress bar and
"12m in" already said it, and the label at the foot said it again once you
tuned in.

Two things surfaced on the way. Every card was sitting 6px short of its own
row, because the wrapper's flex `gap` was being spent on an error slot that
is empty nearly always. And once rows are equalised, a single error notice
stacked below one card would have grown all eighteen — it's laid over the
card now instead.

### Scrolling from anywhere
The shell is a fixed-height column and only the panel inside a tab scrolled,
so the wheel did nothing over the masthead, the library's search row, the
pager, or the margins either side — most of the window. A wheel landing
anywhere with nothing under it is now handed to whichever panel the current
tab scrolls. An open detail sheet keeps its own.

### Channels got colour, and their numbers moved
Each channel carries a hue in `--ch`, spread by the **golden angle** rather
than evenly: eighteen split evenly land 20° apart, which is nothing between
two cards side by side. It only colours what hovering reveals. Contrast came
out 11–14 for titles, 7.5–8.6 for credits.

Names went from `Channel 9 (Directors Cut)` to `Directors Cut #9`, with the
number derived from position in the list rather than typed into each name —
so inserting a channel renumbers the rest instead of leaving two called #7.

### Directors Cut and Type Cast play in order
They're the only channels showing a body of work rather than a genre, and a
body of work has an order. Sorted by release *date*, not year: year is
precise only to twelve months, and the library has two director/year
collisions where that matters. Films with no date sort to the end, because an
unknown year is not year zero.

Ordering alone wasn't enough. Every channel measures its loop from a fixed
point in 2024, but these two rebuild their line-up at midnight when the next
name comes round, and measuring a brand-new list against 2024 drops you at an
arbitrary point in it — the fourth film of nine, most days. They now run from
the same midnight that chose the person, so the morning starts at their first
film. It remains a schedule, not a playlist: tune in at 8pm and you join
Ridley Scott around *Prometheus*.

### The remote
A second pywebview window held above mpv, which is the whole point — mpv
takes the foreground the moment it starts. Channel up/down, volume, mute,
pause, skip, stop, six presets, subtitle and audio track cycling, audio delay,
episode stepping, and a lit display showing what's on.

Notes worth keeping:

- Volume, mute and pause are **asked of mpv**, not remembered. The player has
  its own keyboard and you may well have used it.
- Every button's reply *is* the new state, so the window never shows what it
  hoped would happen.
- Presets default to the first six channels. A remote whose buttons do
  nothing until you've visited a settings screen is one nobody presses twice.
- Track buttons are driven from `track-list`, not mpv's `cycle sub` /
  `cycle audio`. `cycle` decides the ring for itself and always includes
  "off", which is right for subtitles and wrong for audio — a single-track
  file took one press to silence. It now says `NO SUBS` and greys out when
  there's nothing to cycle, which is what the SUBS button not appearing to
  work actually was.
- Selecting a subtitle track also forces `sub-visibility` back on. Choosing a
  track and still seeing nothing is the other way subtitles "don't work".
- Stepping episodes **drops the channel** on purpose. Otherwise the moment
  that episode ended the channel would take the window back.
- Every key starts disabled and shows `Connecting…`. Before the first reply
  the window doesn't know what it's controlling, and a key pressed in that
  gap is a command sent on a guess.

### The control channel, rewritten twice
The original shape — a connection per command, with a blocking read — can't
be bounded: a Windows named pipe has no read timeout, so a caller can only
give up by abandoning the read, and an abandoned read never ends. At four
commands a second from the remote, a busy player leaked threads.

The first replacement was **wrong in a way worth recording**: one permanent
reader thread with separate writer threads on the same handle. A pipe handle
opened without overlapped I/O is *synchronous*, and a synchronous handle
serialises everything — while a `ReadFile` is pending, a `WriteFile` on that
same handle waits for it. So the reader sat waiting for mpv, the writer
waited for the reader, and mpv waited for a command that was never sent. That
is what "the remote doesn't pick up what's on mpv any more" was.

The shape that works: **one connection and one worker thread doing both
halves** — write, then read until that command's answer arrives. Callers
queue a request and wait on an event, so giving up costs a discarded reply
rather than a leaked thread. Proven against a real mpv: twelve concurrent
callers all answered, one worker thread, clean failure when mpv goes away.

Also fixed along the way: closing a pipe handle from another thread is not a
way to cancel a read on Windows, it's undefined behaviour. Only the worker
closes its own connection now.

### The live channel stopped opening a second window
`mpv_play_url` never looked at the window already open — every live tune-in
closed it and spawned a fresh process, and that replacement had **no
`--input-ipc-server`**, so from then on nothing could reach it: not the
progress bar, not the remote, not tuning back off the channel. It loads into
the open window now. The awkward part is yt-dlp: mpv searches its *own* PATH
as it starts, so `mpv_environment()` gives that patched PATH to every launch
rather than only the live one, which is what makes reusing the window
possible at all.

### Subtitle fetching
`FETCH SUBS` on the remote, via OpenSubtitles. Matching uses the file's
`moviehash` — size plus the 64-bit sum of its first and last 64KB — which
identifies the *release* rather than the film, so timings fit instead of
drifting; it falls back to the TMDB id the database already holds. Saved
beside the video as `Film.en.srt`, which mpv's default `--sub-auto=exact`
picks up unprompted, then loaded live so it appears without restarting.

**The quota shapes the whole feature**: five downloads a day without an
account, twenty with a free one. That rules out any sweep through the
library — 2,082 titles would take four months. A file already sitting beside
the video is loaded rather than bought twice.

The password sits in `nextup_config.json` in plain text, by choice, so the
app can sign in on its own. It never reaches the page — the browser is sent
`********` and only learns whether one is set.

### Diagnostics
`faulthandler` is enabled for the life of the app, writing to
`nextup_errors.log`, along with `started` / `closed` lines so a
disappearance can be told from a tidy exit. None of it caught the hang,
because a hang is not a crash — see Planned.

---

## 2026-08-05 — v0.1.1

Version renumbered from 4.0 to 0.1 (and now 0.1.1), which is honest about where
this actually is.

### Playback rebuilt around mpv's control channel
The app used to launch mpv and never speak to it again. It now opens mpv's JSON
control channel — a named pipe on Windows, a unix socket elsewhere — which
changed what's possible in three ways.

- The next title loads into the SAME window instead of closing one and opening
  another. Confirmed by process id: the window survives the swap.
- Position is read live rather than inferred, so the now-playing banner has a
  real progress bar instead of "23 min ago".
- **Watching something start to finish left no trace at all.** mpv only writes a
  watch-later file when you quit part way, so nothing ever set `playcount` —
  0 of 1,566 episodes had one. A series watched straight through never advanced
  and Continue stayed empty. Now the position and duration are observed, so
  "you finished it" is something seen rather than guessed. The old file-based
  reading survives as the fallback when the control channel isn't available.

### Channels now behave like channels
- They advance on their own when a programme ends. Previously a channel played
  one thing and stopped; a Binge block advertised as three episodes played one.
- `--start` turned out to be a GLOBAL option on the mpv instance, not scoped to
  the file it launched with. Tuning in 16 minutes deep therefore dropped every
  following programme 16 minutes in — it inherited the offset you happened to
  join at. Start is now sent explicitly on every load, including as zero.
- Channels also load with `resume-playback=no`, so a half-watched position
  can't override the schedule. Positions are still saved, just not read back.
- A file shorter than its scheduled slot used to make the channel re-select the
  same programme forever. Not hypothetical: 63 episodes have no TMDB runtime
  and are scheduled at a flat 25-minute guess, so anything shorter would loop.
  An advance now knows what just finished and steps past it — or to the next
  episode within a multi-episode block, which is the point of a block.
- Restarting the app used to strand a running mpv: the pipe name carried the
  process id, so a new instance could never reach an old player, and a channel
  would reach the end of a programme with nobody listening. The name is fixed
  now and a leftover player is adopted on startup (an idle one is closed).

### Six new channels, and two fixed
Twelve to eighteen: World Cinema (non-English, on the language a film was shot
in rather than where it was produced), Back in Time (History/War), Trash TV
(nothing matches yet — it's there ready), Non-stop Favs, The Watchlist, and In
Black & White (TMDB's own tagging, not a guess from the year).

- Binge blocks went from three episodes to six.
- Type Cast excludes ensembles. Billing order alone couldn't do it — Robert
  Downey Jr. heads the cast list of Iron Man and Avengers alike — so it counts
  how many of the next four names are top-billed somewhere else in the library.
  Avengers scores 2, Iron Man 1. The cost is that genuine two-handers go too.

### Data integrity
- **A folder change duplicated the entire library.** Media folders moved from
  `E:/Torrents` to `E:/Torrents/MOVIES` + `/TV`; a row is identified by its path
  string, so re-walking produced `E:/Torrents/MOVIES\x.mkv` where the old rows
  said `E:/Torrents\MOVIES\x.mkv` — different strings, same files, everything
  added twice. The old rows should then have been purged, but that was over the
  mass-delete threshold, so the guard held them and both sets survived. Merged
  rather than picking a side, so a rating made on either copy carried across;
  verified zero loss against a backup. Paths are normalised at discovery now.
- A scan against an unreachable folder used to read an unplugged drive as an
  empty one and delete the lot. It stops instead. A second guard holds back any
  removal of more than half the library and says so.
- Parser: `Movie <title> - <show>` and `Special <title> - <show>` naming,
  `SxxSPxx` specials (filed as season 0 rather than as phantom films), release
  junk left stranded in front of a year ("Jackass Number Two Unrated"), and
  misspelled extras folders — a real "Featuretts" folder was putting two True
  Detective featurettes in the library as films. Diffed old against new across
  all 2,082 paths first: exactly 8 changed, all intended. Unidentified films
  went 7 to 0.

### Favourites
A flag of its own, not derived from a high rating — a score says how good
something is, a favourite says you'd put it on again, and the two part company
constantly. Marked from a tile or a detail page, with its own Library section
(films and shows together), its own channel, and a richer page carrying the
facts TMDB actually knows plus cast portraits. Clicking any name opens that
person's own page: photo, biography, and everything of theirs you own.

### Recommendations
- They survive a restart now. Previously closing the app threw away a few
  hundred TMDB lookups, including the missing-episode list, which barely
  changes week to week.
- **The taste profile had two real faults.** Its strongest signals were
  production facts — "based on novel or book" scored second only to "dystopia",
  high purely because it's common. Features are now scored on how well their
  films do on average, scaled by how many stand behind them. And the midpoint
  was hardcoded at 5.5: across 289 generously-rated films nothing ever landed
  below it, so the dislike filter had never once done anything. It uses your own
  average now. The sample also went from 45 films to 250 — that cap existed to
  limit TMDB calls, which are entirely cached these days.
- Sortable by match, TMDB rating or year; hovering a suggestion fetches its
  director and cast on demand.

### Offline
Posters are downloaded and served locally, so the library works with no
connection — 2,089 images, about 57MB. Backdrops and cast portraits follow the
heart: mark a favourite and its pictures come down. Everything except artwork
was already local.

### The window
- No console window: launched through `pythonw` via a proper shortcut.
- Frameless, with a title bar the app draws itself. Dropping the native frame
  also drops `WS_THICKFRAME`, which quietly made the window unresizable; that
  one style bit is put back after the window opens.
- Branding moved into the title strip, which was empty bar anyway — the
  masthead went from 149px to 43px.
- The page no longer scrolls as a whole. Only the content inside a tab does, so
  in the library the scrollbar starts at the tiles. The bar itself is restyled
  with a transparent track.
- Two silent CSS traps worth remembering: custom properties don't reach inside
  scrollbar pseudo-elements, and setting `scrollbar-width`/`scrollbar-color`
  alongside `::-webkit-` rules makes the standard ones win outright.
- The Library's Films/TV switcher had no CSS at all and was rendering as raw
  grey browser buttons.
- Text selection was off everywhere because pywebview defaults `text_select` to
  False. The watchlist and favourite toggles on a tile were unclickable because
  the hover overlay had `pointer-events:none` and the buttons inherited it.

### Packaging
A self-contained build in `Next Up 0.1.1`: the app, mpv, yt-dlp and the TMDB
key, needing nothing installed. Two bugs found only by running the packaged
build — a second instance silently hijacked the first one's port (on Windows
`SO_REUSEADDR` lets a bind succeed rather than fail), and with `--noconsole` any
startup failure produced no window and no message at all.

---

## 2026-08-04

### Data integrity & library scanning
- Fixed a `shutil` import bug that would crash mpv detection on machines where mpv wasn't in a hardcoded guess path.
- Fixed a filename parser bug: episodes with lettered sub-parts (SpongeBob-style `S01E17A`) were being misfiled as junk movies.
- Found and fixed a major show-matching bug: files like `S01E02 Title - ShowName.mkv` or folders like `Game of Thrones Season 1` were creating duplicate per-season "shows," some mismatched to totally unrelated TMDB titles. Migrated ~43 bogus entries back into their correct shows, preserving all ratings/watch history.
- Found zero of 1,566 episodes ever had runtime data stored — this was the actual root cause of "TV shows aren't appearing on Channels." Fixed the enrichment and backfilled it.
- Found TV shows never had cast or creator data populated either (columns existed, nothing wrote to them). Fixed and backfilled — 53/59 shows now have cast, 41/59 have creators.
- Excluded torrent-client staging folders (`Incomplete - Delete`, `_EXTRAS_QUARANTINE`) from scanning.
- Caught and fixed a real mistake: an early version of the incomplete-folder fix deleted all 12 BoJack Horseman episodes from the database as a side effect. Caught it, confirmed the files were untouched on disk, and restored the entries. Root cause fixed so it can't happen again.

### "Now" picks & recommendations
- Fixed Tonight picks being ~90% TV — two causes: no "rated = seen" filter existed for shows (only films had one), and TV rates structurally higher than film on TMDB, so a shared ranking always favored it.
- Switched from "hide anything rated" to "only hide poorly-rated (below 5) — a high rating is a reason to resurface as a rewatch, not hide."
- Fixed the rewatch mechanism over-correcting (dominating results) by reserving it a fixed minority share of the draw rather than letting it compete openly.
- Added a Watchlist: toggle from tiles or detail sheets, its own Library filter, and a scoring boost in Tonight picks.
- Added an Actors section to Recommendations, mirroring Directors (owned actor gaps, lead/prominent roles only).

### Channels (built from scratch this session)
- 12 channels total: Everything, Universal (family), True Life (docs), Action, Comedy, Al Jazeera Live, Saturday Morning, Cult Classic, Directors Cut, Type Cast, Anime, Binge.
- Deterministic scheduling: each channel loops from a fixed anchor date, so "what's on" is consistent and mpv seeks to the right point when you tune in.
- Comedy excludes anything also tagged Thriller/Horror (was letting Parasite/Bugonia through on a technicality).
- Universal tightened to Family/Kids specifically (was letting South Park/Invincible through on "Animation" alone).
- Directors Cut / Type Cast rotate to a different person daily; Type Cast requires true lead billing (Gwyneth Paltrow no longer counts from Iron Man).
- Cult Classic uses vote count (new data) to find well-regarded-but-niche films.
- Binge is TV-only, shows rated 7+, three episodes per block; other channels single episodes except Universal/Anime (paired).
- No two channels play the same thing at once; "up next" never repeats what's "on now."
- Added a live channel (Al Jazeera via YouTube) with proper yt-dlp dependency detection and a PATH fallback fix so it survives winget installs happening after the app started.
- UI: whole card is clickable ("Watch"), hover reveals director/creator, cast, and rating.

### Movie detail page
- Full untruncated plot + tagline (was cut off at 300 chars).
- Cast & Director section with click-through to other owned films by that person.
- Similar Films section (shared keywords/genre against your own shelf).
- Laid out as three panels — main info full-width, Cast and Similar split side-by-side below it.

### Playback
- Starting anything new now closes whatever mpv was already playing first — gracefully (a close request, not a force-kill), so the old file's resume position still saves correctly.

### UI/UX polish
- Library: real pagination (no more infinite scroll), sticky header, fixed "Recently added" sort, randomized (and stable-while-rating) Rate queue.
- Rating control: each half-star is now a real distinct element — no more ambiguous "7.5 or 8" tooltip.
- Nav tooltips, "Up Next" renamed to "Recommendations."
- Logo added as header icon and favicon.
