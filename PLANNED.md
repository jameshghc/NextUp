# Planned

Everything wanted but not built, most pressing first. `DEVELOPMENT_NOTES.md`
is the record of what *has* been done; this is the list of what hasn't.

Read this at the start of a session. Anything asked for but not started
belongs here rather than in a conversation, because conversations get
summarised away and files don't.

---

## Picky-user QA findings for 0.2 (2026-10-20; screenshots in docs/mockups/shots/qa-*.png)

The four glaring ones were fixed in 0.2.0; these may be partly done.

**Worth fixing**
- "1 shows" in the phone header, and "a 8" → "an 8".
- Streamable tiles say "ON DESKTOP-O2K6QB8": say "ON THE PC".
- The phone header's wordmark wraps ("NEXT / UP"): nowrap it, and
  shorten the stats on the phone.
- PC tile hover: the blurb is clipped with no fade, the caption shows
  through under FAVOURITE, and "97 / min" wraps.
- Phone peek: DETAILS and ON PC touch with 28px buttons, and the caption
  ghosts through.
- Detail sheets: mismatched button heights and gaps. The show sheet has
  no top-level PLAY / CARRY ON. The phone's rating half-steps are 9px
  wide. No ON PC in the phone details sheet.
- Classic Appearance: the disabled sliders' thumbs aren't dimmed, and
  the slider track is faint.
- History: "watched to the end" sits beside "35%", and in-progress shows
  in the error colour (rust).
- The subtitles button is called both FETCH SUBS and FIND.
- Rate: the loudest control is "Refresh queue", and BACK is enabled on
  card 1.

**Nitpicks:**
- double ellipsis ".…"
- Play / PLAY / Resume capitalised three ways
- sub-tab styles mixed, lower-case tags
- "For you" wording on Rate
- "Directors Cut" missing its apostrophe, and "0m in"
- the phone Channels REMOTE button opens the desktop popup
- tooltip casing
- mixed apostrophes
- the film sheet repeats "nothing else of theirs here", "11.0x", money
  formats, and CLEAR shows when not rated
- Recent activity out of order, and episodes listed without the show name
- the "‹" in the chooser is almost invisible
- "♪ ENG" accent-coloured in Classic
- sheet widths differ

- Deferred: the remote's minors (see DEVELOPMENT_NOTES v0.2.0), the odd
  phone profile name, and the LG TV options (a Google TV stick running Next
  Up, or the TV's own player over DLNA).

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

## Android: deferred minors from the step 3 review (2026-10-08)

- `check_storage` hard-codes port 8770;
- no Android ≤12 storage permission;
- `first_run_library` re-adds the folder if emptied;
- the APK version is duplicated from `APP_VERSION`;
- `check_page.js` needs Node 22+;
- snapshot import looks in `HERE`.

## Next up (parked 2026-10-03)

- **Al Jazeera Live may need yt-dlp updated before it plays** (`winget
  upgrade yt-dlp.yt-dlp`); YouTube refused streams to the old one. (Cold
  Ones, the other YouTube channel, was dropped in 0.2.2.)
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

**How:** `git pull` (the repo is on GitHub now), or copy `nextup.py` across
and run it with `run.sh`. Not the `mac/` folder — the
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

### The old versions archive

`Old versions and extras` is 1.45GB and nothing current depends on it.
Pruning is a decision, not a tidy-up — those folders are there because they
were asked to be kept. The two safe wins when the time comes:

- the **extracted** Mac copy, ~380MB, broken by the Windows unzip (its
  working zip stays)
- superseded release builds and zips, ~700MB

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
