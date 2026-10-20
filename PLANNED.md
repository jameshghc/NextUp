# Planned

Everything wanted but not built, most pressing first. `DEVELOPMENT_NOTES.md`
is the record of what *has* been done; this is the list of what hasn't.

Read this at the start of a session. Anything asked for but not started
belongs here rather than in a conversation, because conversations get
summarised away and files don't.

---

## The look: grey glass (built in v0.1.77: the user chose C)

`docs/mockups/glass-ui.html` (serve with the "mockups" launch config, port
8778) has A (today), B (smoked glass) and C (frosted glass). Screenshots are
in `docs/mockups/shots/`. Once the user picks, build it as a choice under a
new Settings → Appearance tab, keeping today's look available.

## A remote for the PC, in the phone app (built in v0.2.0; the sketch below is history)

Control what's playing on the PC from the phone, on the same Wi-Fi. It
builds on two things that exist:
- the PC's own remote (`remote_state`, `/api/remote/*`: play/pause,
  volume, mute, audio delay, subtitle and audio tracks, next episode, skip,
  channels, stop);
- the Wi-Fi link (`PhoneHandler` on 8790, the token from SEND MY LIBRARY,
  `pc_link_call`).

1. **PC: `/phone/remote/*` on `PhoneHandler`.** Bearer-gated, home network
   only, the same as every phone route.
   - An explicit list: `state`, `toggle`, `volume`, `mute`, `delay`,
     `subtitles`, `audio`, `seek`, `episode`, `skip`, `channel`, `stop`,
     `afk` (answer "are you still watching?").
   - Each calls the same function the desktop remote route does, so the
     two can't drift. Nothing else from the desktop server is exposed.
   - Every press calls `seen_you()`, so using the phone remote counts as
     being there for the sleep timer.
2. **PC: two additions to `remote_state`:**
   - `position` and `duration`, so the phone can draw a seek bar;
   - the AFK question, so the phone can show it.
3. **Phone server: `/api/pcremote/*`.** It passes each call to the PC via
   `pc_link_call`, so the token never reaches the page.
4. **Phone page: a Remote screen.** A fifth tab, or a button in the
   masthead that only shows while the PC answers.
   - Now playing: art, title, a seek bar with times.
   - Big play/pause, back 10 s / forward 30 s, volume with mute.
   - Audio delay ±50/100 ms (remembered per film, as on the PC).
   - Subtitles and audio track: tap to cycle, showing the language.
   - Next episode and skip, shown only when they apply.
   - The six channel presets, and stop.
   - "Are you still watching?" appears there with STILL HERE / THAT'S
     ENOUGH.
5. **Battery.** The state is asked for once a second ONLY while the Remote
   screen is on screen and the app is in front. It stops on hide, and
   nothing runs in the background.
6. **Later, if wanted:**
   - "Play on PC" from a tile's peek, starting it on the PC instead of the
     phone (`/phone/remote/play {key}`).
   - The phone's own volume buttons driving the PC's volume while the
     Remote screen is open.
7. **Tests.** The `/phone/remote/*` list (and that nothing else is
   reachable), the proxy, and the page source checks. The seek and AFK
   fields are tested in `wifi_stream_test` style against a loopback link.
   Then a real try on the S24.

## The user's list, 2026-10-19

Items 1–4 were done in v0.1.76. Item 5 (the look) is next: show mock-ups
first.

1. **"Are you still watching?" never stops a film.**
   - By design it only asks at a hand-over (between episodes or queue
     items), so a lone film always plays out.
   - Ben-Hur ran to the end on 17, 18 and 19 Oct while the user slept, and
     was marked watched twice.
2. **Films missing from Now's "Continue" strip.**
   - Not the sleep timer. `build_continue` sorts every half-watched episode
     (sort 1) ahead of films (sort 2) and cuts the list at 6.
   - With 30+ shows in progress, films never make it in. `/api/resume`
     has 88 films and 32 shows.
   - **Fixed:** Now's strip uses the resume row (newest first, films and
     TV, up to 24).
   - **Found while doing it (fixed in v0.1.76 since):** if mpv's resume folder is
     missing, `read_resume_points` returns nothing and
     `sync_playback_state` reads every watch point as "watched to the end".
     It wipes them all, adds a play, and stamps them played now. A missing
     folder should mean "don't know", not "all finished".
3. **Settings in tabs** instead of one long scroll. There are nine sections
   today.
4. **The Now page:**
   - the genre chooser moves up, and the Continue strip gets shorter to make
     room;
   - choosing a genre mustn't reset the scroll position;
   - the mouse wheel over the Continue strip scrolls it sideways.
5. **Visual customisation in Settings,** starting with a more transparent
   grey UI.

## To check first, 2026-10-12: "Continue where you left off" with Wi-Fi streaming

The user wants to see how Continue behaves for streamed films and episodes.
Likely gap, from reading the code (not yet confirmed):
- Streamed watch points live only in history, by tmdb identity
  (`elsewhere_progress`), because there's no local row.
- Continue and the "progress" shelf are built from local rows'
  `in_progress` (`nextup.py` ~5366, ~5384), and elsewhere rows always
  have `in_progress: False`.
- So a film stopped halfway over Wi-Fi probably doesn't show in Continue
  on the phone. The tile's peek PLAY does resume from the right point.

Check on the S24, and with `tests/phone_serve.py --with-pc`:
- stream a film, stop halfway, and look at Continue on the phone;
- check the same film on the PC's Continue after the Wi-Fi swap;
- check a streamed episode, and what "next episode" Continue offers.

If it's missing, fill `in_progress` and `percent` on streamable elsewhere
rows from `elsewhere_progress`, and let Continue include them while the PC
is up.

## Streaming from the PC over Wi-Fi — built (v0.1.75, 2026-10-11)

Built; see DEVELOPMENT_NOTES v0.1.75. Still to do: the user to restart the
PC app, SEND MY LIBRARY once (that pairs the phone), and try it on the
real network. Not built (out of scope): streaming away from home, and
phone-side code pairing.

## Android app: where it stands (2026-10-08)

- **Done:** step 1 (PC phone link, v0.1.48), step 2 (toolchain in
  `X:\DevTools`), step 3 (v0.1.49): Next Up runs on the test phone, a
  Galaxy S21 Ultra (Android 15), as `app.nextup.mobile`. Data lives in the
  app's private folder, films in `Movies/Next Up/` (video permission
  allowed by the user). Build with `python android\build.py`. Check with
  `android\check_device.py`, `check_page.py` and `check_storage.py`.
- **Next, spec step 4:** pairing with the PC from the phone, the snapshot,
  downloads, and sync. Then **step 5**, playback through mpv-android,
  which replaces the desktop Play/mpv wording. Then **step 6**, the phone
  layout pass: hide the docking station, sorter and remote; bottom nav;
  the "U0_a429"/"localhost" names; scan after the permission is granted;
  external links; Back button; `allowBackup`.
- **Deferred minors from the step 3 review:**
  - `check_storage` hard-codes port 8770;
  - no Android ≤12 storage permission;
  - `first_run_library` re-adds the folder if emptied;
  - the APK version is duplicated from `APP_VERSION`;
  - `check_page.js` needs Node 22+;
  - snapshot import looks in `HERE`.

## Next up (parked 2026-10-03)

- **Cold Ones channel needs yt-dlp updated before it plays.** Built and
  tested in v0.1.47; the list loads, but YouTube refuses streams to the
  installed yt-dlp (2026.07.04, over 90 days old): `winget upgrade
  yt-dlp.yt-dlp`. Then tune in for real and check the seek lands mid-video.
  Al Jazeera Live is probably refused the same way.
- **A traditional TV-guide layout for Channels?** Asked, not yet answered.
  Channels run nose to tail from a fixed epoch, so a grid of what's on next
  across every channel is computable — the open question is the design.
- **YouTube next moves:** history/docs creators feeding True Life and Back
  in Time (capped share), and a YOUTUBE shelf beside Favourites.
- **From the watch-data review:** make the Now tab's "rated 8+" bonus
  relative to the user's own scale (217 of 316 rated films clear 8); set the
  "still watching?" clock bands around their real hours (most viewing ends
  3-7am); two films played since 22 Sep have no finished/stopped row —
  check before trusting Watch Score for films.

---

## Always: the Mac is behind

**Do this whenever there's time.** The MacBook is on **v0.1.21**. Everything
since exists only on the Windows copy:

| | |
|---|---|
| v0.1.22 | sharing history, ratings, watchlist and resume between computers |
| v0.1.23 | the header reshuffle |
| v0.1.24 | shows for you, and what would fill a thin channel |
| v0.1.25–26 | the right-click menu and the docked queue |
| v0.1.27 | the "Pick something" rework |
| v0.1.28–30 | the port fix, dead code swept out, browser cache reclaimed |
| v0.1.31 | the SORT NEW DOWNLOADS button |
| v0.1.32 | history opening on a week, and a tab press that goes home |
| v0.1.33–34 | "are you still watching?" |
| v0.1.35 | the resume tile follows the Films / TV shows tab |
| v0.1.36 | Favourites and Watchlist shelves actually filter again |
| v0.1.37 | no TMDB score on the Rate tab |
| v0.1.38 | the Rate card: artwork, one size, full description, tagline tile |
| v0.1.39 | a sort keeps the better copy, and asks before binning the other |
| v0.1.40 | shows follow the episode you watched last; favourites suggest any episode |
| v0.1.41 | missing episodes re-checked against the library every time |
| v0.1.42 | a hidden Watch Score for every film and show |
| v0.1.43 | a design pass on Settings |

**How:** copy `nextup.py` across on its own. Not the `mac/` folder — the
copy in `Old versions and extras` had its bundled Python broken by a
Windows unzip, and the only good one is inside the original Mac zip.

Two things to check once it's over there: sharing needs turning on in
Settings on that machine too, and the sorter button will want a downloads
folder that exists on the Mac.

---

## "Are you still watching?" — the second iteration

**Built in v0.1.33**, after a night when episode 1 of My Hero Academia turned
into the whole season. What it does now: playback that carries on by itself —
an episode run, the queue, a channel — stops at a hand-over and asks, once
nothing has been touched for longer than that time of day allows. Settings
live under Settings › *Are you still watching?*

Deliberately left out of the first iteration, in roughly the order they'd be
worth adding:

- **The remote window doesn't show the question.** It's the one window that
  sits *above* mpv, so it's the obvious place to answer from the sofa. Cheap
  to add: it already polls once a second.
- **Nothing asks during a single very long film.** Asking only at hand-overs
  was the right first rule, but a four-hour film with nobody in the room
  still plays to the end.
- **Only the keyboard counts as being there, not the mouse.** Pausing and
  seeking in mpv are noticed; moving the mouse over its window isn't.
  mpv has a `mouse-pos` property, so this is one more poll if it matters.
- **How long you've been watching isn't an input.** Four hours in, at any
  hour, is a different proposition from twenty minutes in. Clock bands alone
  caught the night that prompted this, so it may never be needed.
- **The band boundaries are fixed** at 6am, 6pm and midnight. Only the
  lengths are adjustable.
- **It doesn't put the machine to sleep**, it only stops holding it awake.
  Windows' own timer does the rest.

---

## Waiting on a decision: a written one-liner for every film

Asked for 2026-09-23: a line like *"DiCaprio stars in a film about Wall
Street"* on the Rate card. The card has TMDB's own tagline in that spot
for now (539 of 558 films) — but that is the studio's poster line ("Earn.
Spend. Party."), not a description of the film.

TMDB doesn't have the asked-for kind. Options:

- **Template from cast, director and genre** — "Leonardo DiCaprio in
  Martin Scorsese's crime comedy". Free, instant, always correct, but no
  *about*: that part needs the keywords, which are too unreliable (*Babylon*
  leads with "elephant").
- **A language model writes them once**, from the title, cast and plot
  already in the database, cached in a new column so each film is only
  ever written once. Reads exactly like the example. Needs an Anthropic API
  key in Settings; the whole library would cost pennies with a small model.
  Shows could have them too.

---

## Waiting on a decision: the rest of the Settings design pass

The first ui-designer run (2026-09-28) fixed eleven small things and brought
these back rather than build them, because they change behaviour or layout:

- **Saving one card throws away unsaved edits in the others.** Each SAVE
  reloads every field from the saved settings, so edit the folders, save the
  TMDB key, and the folder edits silently vanish. Fix: one SAVE for the page,
  or reloading only the fields that weren't being edited.
- **"saved" appears even when saving failed** — the result is never read.
- **The docking station duplicates the Library's own select-and-copy tray**
  (same cart, same drives). The Settings card could become two lines and a
  button into Library select mode — once it's checked nothing is lost.
- **The page is long and ungrouped**: seven cards, about six screens. A
  regrouping — Library, Playback, Keys, Devices, Your data — with a small
  index at the top.
- **Recent activity shows episode titles without their show** ("I CAN DO
  WHATEVER I WANT." — of what?). Needs the show name sent with it.
- Small: "1830 events" where the card says "things"; the minutes fields
  don't say "min"; the TMDB key box runs the full card width.

---

## Low priority — wanted eventually, no rush

### A copy on GitHub

The project has had a local git history since 2026-09-27: every change is
saved as a snapshot, on this machine only. The next step is a private copy
on GitHub, which would mean:

- **the Mac fetches the latest version in one step** instead of files being
  copied across by hand — the fix for the item at the top of this list
- a copy that isn't on the X: drive

Needs you to make a GitHub account and a **private** repository; Claude
can't create accounts, and will ask before uploading anything. The private
files — config, library, test scratch — are already excluded and were
checked before the first snapshot.

### Your phone as a way in

**Decided 2026-10-07:** a real Android app (BeeWare APK) for the user's
S24 Ultra, Mac-style with its own library stored on the phone, paired with
the PC over home Wi-Fi for the snapshot, sync and downloads. Design:
`docs/superpowers/specs/2026-10-07-android-app-design.md`. The options
below were the fork before that decision:

- **A phone-shaped page served over Wi-Fi, playing on the PC.** The cheap
  one. `/remote` already exists and already carries a viewport meta; this
  widens it into browsing, queueing and rating. Add-to-home-screen makes it
  feel like an app without an APK.
- **The same, plus video on the phone.** 80% of this library is `.mkv`,
  which Android browsers won't play — those would hand off to VLC, and only
  the ~460 MP4s would play in the page itself. Transcoding is a much bigger
  job.
- **A real APK.** Weeks: a Python build chain on Linux, a rewritten UI,
  mpv-android, and the PC still holds the files. Advised against.

**Settle first, whichever way it goes:** the server binds `127.0.0.1` only,
and there is **no authentication anywhere** — some endpoints move files to
the bin. A phone reaching the app means a LAN bind, a PIN, and the
destructive routes closed to it.

### The old versions archive

`Old versions and extras` is 1.45GB and nothing current depends on it.
Pruning is a decision, not a tidy-up — those folders are there because they
were asked to be kept. The two safe wins when the time comes:

- the **extracted** Mac copy, ~380MB, broken by the Windows unzip (its
  working zip stays)
- superseded release builds and zips, ~700MB

---

## Decisions waiting on you

### ~~X-Men '97 is in the library twice~~ — done, 2026-10-10 (v0.1.65)

Decided by the user ("solve it for good"). Merged with a backup first; see
DEVELOPMENT_NOTES 2026-10-10 for how, and what stops it coming back.

---

## Ideas, unranked

### A front door: launcher, installer, and a login

Something that runs *before* the window — sets the machine up on first run,
works out which platform it is on, then opens the right thing.

**The installer is the strong idea.** It is what `mac/` does by hand
already: carry the runtime, check it, start. Generalising that into a
first-run step that verifies Python and mpv, fetches what is missing and
reports what it cannot fix would remove the entire class of "it doesn't
start".

**The platform detection mostly exists**, in the only place it can:
`nextup.py` is the same file on both systems and already branches on
`os.name` everywhere it matters. What cannot be unified is the double-click
target — Windows needs a `.exe`, macOS needs a Mac executable bit. Two entry
points is the floor, not a shortfall.

Worth remembering: **NextUp.exe is a PyInstaller bundle with its own frozen
copy of the source.** It does not read the `nextup.py` beside it. Any
launcher that "chooses the right version" is choosing between a frozen build
and a live script, and those drift the moment either changes.

**The login screen is the weak one.** For one person across several devices
it protects nothing — the library, the ratings and the files are all
readable next to it. Build it as a *profile picker* — who is watching, whose
ratings these are — and it earns its place. Build it as authentication and
it is a lock drawn on a door. (The profile picker exists; this would be the
honest remainder of the idea.)

---

## Watched, not built

**mpv crashes by itself** with an access violation (0xc0000005), twice on
2026-08-06 at the same fault offset. That is mpv v0.41.0 faulting inside
itself — nothing of ours on the stack, nothing to fix unless it recurs.

**A first-chance `0x8001010d` COM exception** during WebView2 creation gets
logged by faulthandler and is harmless.
