NEXT UP  v0.1.42
A film and TV companion for your own media folders.


RIGHT-CLICK, AND THE QUEUE
--------------------------
Right-click any poster in the Library for:

  Play               start it now (a show starts where you got to)
  Play next          put it straight after whatever is on
  Add to queue       put it at the end of the queue
  Favourites and watchlist, on or off
  Details            the film's or show's own page

Anything queued appears in a panel down the right-hand side of the window,
on every tab, and each thing starts by itself when the one before it
finishes. Drag to reorder, or use the arrows that appear on hover; the
play button on a row starts that one now. Queueing a show queues the
episode you're up to, and queueing it again queues the one after that.

A few rules, so it never surprises you:

  - It moves on only when something FINISHES. Closing the player stops the
    queue rather than skipping to the next thing.
  - Channels are left alone. A channel carries on with its own schedule,
    and the queue waits until you're back on something you picked.
  - SKIP on the remote plays the next thing in the queue.
  - The queue is kept when you close the app.
  - On a narrow window the panel tucks into a tab on the right edge
    instead of squeezing the page; click it to slide the queue out. On a
    wide one, the arrow at the top of the panel tucks it away by hand.


ARE YOU STILL WATCHING?
-----------------------
Episodes roll into the next one, the queue starts the next thing, and a
channel never stops. Fall asleep and a whole season can play out - and mpv
holds the PC awake while it does, so it won't drop off either.

So when nothing has been touched for a while - no button here, and no pause
or seek in mpv itself - the next thing is held back and Next Up asks. Say
STILL HERE and it carries on with exactly what it was about to play.
Say THAT'S ENOUGH, or say nothing at all, and the player closes.

It only ever asks BETWEEN programmes, never over one, and only when
something would actually have followed. Nothing you slept through is marked
as watched, because it never started.

How long is "a while" depends on the time of day, since falling asleep is a
night-time problem. Three lengths, in Settings:

  Daytime (6am-6pm)         4 hours
  Evening (6pm-midnight)    2 1/2 hours
  After midnight            1 1/2 hours

The one that counts is the one for the time the question would be asked,
not the time you pressed play - put a film on at half eleven and it is
judged as two in the morning. Set any of them to 0 to never be asked then,
or untick the box to switch the whole thing off.


SORTING NEW DOWNLOADS
---------------------
Settings, beside SCAN MY FOLDERS: point "Downloads folder" at where finished
downloads land (the app suggests it if your library folders sit inside it),
then press SORT NEW DOWNLOADS.

It never moves anything without showing you first. The button asks the
process_new_movies.py sorter kept in that folder what it would do, and lists
it: each release and where it would go, plus anything held back for still
downloading, having no video file yet, or being an incomplete season pack.
Only when you press SORT THEM does anything move.

Then it finishes the one job that script leaves undone. The script names
episodes "S05E01 - Show.ext" because it has no way to look titles up; Next
Up fills them in from TMDB, so they land as "S05E01 Crimes of the Hot -
Futurama.mkv". Nothing is invented: an episode TMDB doesn't know keeps the
name the script gave it. Afterwards the library is scanned so the new
things appear straight away.

Downloaded something you already have? The better copy wins - higher
resolution first, then higher bitrate if the two are otherwise the same -
and the other copy is moved into a _DUPLICATES folder in the downloads
folder. Nothing is ever deleted by the sort. When a better download replaces
one of yours it takes your file's name, so your rating, watched history and
episode title stay with it. The preview says up front when a download
overlaps what you have ("YOU ALREADY HAVE 3 OF 4 EPISODES").

Whatever is set aside then waits under the sort button in Settings, with
what each file is and why it lost, and a MOVE TO BIN button. Nothing leaves
until you press it, and then only as far as the Recycle Bin. That includes
anything set aside by a sort run outside the app, such as a scheduled one.

The sorter itself needs Python with openpyxl, and ffmpeg/ffprobe on PATH.
Next Up finds them; if it can't, it says which is missing rather than
failing silently.


SHARING BETWEEN YOUR COMPUTERS
------------------------------
Your history, ratings, watchlist, favourites and where you stopped can be
kept the same on every computer you run Next Up on, through a cloud folder
they all sync — OneDrive, Dropbox or iCloud Drive.

Setting it up: the first time Next Up finds one of those folders it asks,
once, at the top of the Library. Say yes on each computer. It is also under
Settings > Sharing between devices, where you can pick a different folder
or stop.

After that there is nothing to do. Everything you watch, rate or add is
written to this computer's own file in "Next Up sync" inside that folder;
each computer checks for the others' files when it starts and once a minute
while it's open. Stop a film on the Mac and the PC offers to resume it from
the same place — as long as that film is in both libraries.

Worth knowing:

  - The sync app itself (OneDrive, say) must be running and signed in to
    the same account on every computer. Settings says so if it isn't.
  - Films and episodes are matched by their TMDB id, never by title. Things
    the other computer hasn't got still show in History, marked with the
    computer they were watched on, and can't be played.
  - If both computers change the same thing, the later change wins.
  - It isn't instant: allow a minute or so between computers.
  - Your library itself is never put in the cloud folder, and stopping
    sharing leaves the files already there alone.


THE SAME FILM, TWICE
--------------------
A DUPES button appears in the Library toolbar, next to the refresh arrow,
whenever one film has more than one file. It only appears when there is
something to look at.

It opens a review screen, not a cleanup button. Each film shows every copy
with its size, resolution, codec and whether it is HDR, and suggests which
to keep: higher resolution first, then the larger file. Two things it will
NOT do:

  - guess when the copies are the same size to the byte. That means one file
    copied twice, not two encodes, and no rule can pick between them. It
    says so and waits for you.
  - treat a filename with no resolution in it as though it were worse than
    one that has. Unknown is unknown.

Then two buttons:

  REMOVE FROM LIBRARY   the file stays exactly where it is; the library
                        forgets it, and the next scan does not pick it up
                        again. Use this when you want the tile gone but the
                        file kept.
  MOVE TO BIN           the file goes to the Recycle Bin (Windows) or the
                        Trash (Mac), where you can still get it back, and
                        the library forgets it afterwards. Never a straight
                        delete, and never before the bin has accepted it.

On a Mac, a drive macOS has mounted read-only — which includes every NTFS
drive — cannot have anything deleted from it. MOVE TO BIN is disabled in
that case and says why. REMOVE FROM LIBRARY still works, because it does not
touch the disk.

Matching is by TMDB id, so two files are only ever called duplicates when
they are the same film, not merely similarly named.


WHO'S WATCHING
--------------
The app opens on a profile screen: who is watching, and which machine this
is. Pick a face to go in. Tick "go straight in next time" and it stops
asking; the screen is still there under Settings whenever you want it.

A profile is a PERSON, not a device. One of you across two machines is still
one of you — make a profile mean a machine and your ratings end up split in
half. The machine has its own name, set by clicking it on that screen, and
that name is what the OTHER device shows on greyed-out posters (see CARRYING
YOUR LIBRARY). It starts as the computer's own name.

Ratings and history are shared between profiles at the moment. The screen
says so rather than implying otherwise; separating them properly is a change
to where every rating is stored and is not done yet.


CARRYING YOUR LIBRARY TO ANOTHER DEVICE
---------------------------------------
A library is keyed by file path, so a second machine starts empty and there
is no way to see what you own without walking to the other room. A snapshot
fixes the looking, not the watching.

On the machine with everything, export one:

    http://127.0.0.1:8770/api/library/snapshot

Save that file as "nextup_snapshot.json" in the app folder on the other
machine, then POST to /api/library/snapshot/import (or press the button on
the Settings tab when it lands there).

Your whole catalogue then shows up in the Library: titles, years, episode
counts, your ratings. Anything the second machine hasn't actually got is
greyed out, badged with the name of the machine that has it, and can't be
opened or played — because it isn't there.

Matching is by TMDB id, never by filename. Two files of one film collapse
into a single entry, so a 1080p and a 4K copy of the same thing count once.

What doesn't travel yet: ratings made on the second machine don't come home,
and a snapshot is a moment in time, so it drifts until you export a new one.


WHAT IT DOES
------------
Point it at the folders where you keep your films and TV, and it builds a
library out of them. Then:

  Now              what to watch tonight, and plays it
  Library          everything you own, searchable, with favourites
  History          what you watched, when, and how much of it - one row per
                   thing, holding every sitting you gave it, with RESUME and
                   MORE so it's a place you can start something from
  Recommendations  what's worth getting hold of next - the episodes your
                   seasons are short of, film series you own part of,
                   directors and actors you collect, films and shows picked
                   from your own ratings, and what would fill a thin channel
  Drives           what's on a plugged-in drive, shown like the library
                   (Windows and macOS; a drive macOS has mounted read-only,
                   which includes any NTFS drive, isn't offered as a target)
  Rate             work through what you haven't scored
  Channels         twenty-one channels running on a loop, TV-style

Everything runs on your own machine. Nothing is uploaded anywhere.


GETTING STARTED ON WINDOWS
--------------------------
1. Unzip this folder somewhere you can write to (see WHERE TO PUT IT).

2. Double-click NextUp.exe.

   Windows may say "Windows protected your PC". That's because the app isn't
   code-signed, not because anything is wrong with it. Click "More info",
   then "Run anyway".

3. Go to the Settings tab (the gear, top right).

4. Under "Your folders", type the folders where your films and TV live, one
   per line. For example:

       D:\Films
       D:\TV

   Point it at the folders that actually hold the media. If you later change
   these, the app copes - but a scan finds files by their full path, so it's
   worth getting them right the first time.

5. Press SAVE, then press SCAN MY FOLDERS.

The first scan takes a few minutes on a large library: it looks up every
title and downloads the artwork so the app works without an internet
connection afterwards. After that it only looks at what's new.


GETTING STARTED ON A MAC
------------------------
Nothing to install. This copy carries its own Python and its own mpv in the
mac/ folder, so there is no Homebrew step and no admin password.

1. Put this folder somewhere you can write to (see WHERE TO PUT IT).

2. Double-click "Next Up.app".

   The first time, macOS may say it can't verify the developer. Right-click
   it and choose Open instead, and it will remember from then on.

   ("Next Up.command" does the same job from a terminal window, and is what
   to reach for if the app ever won't start and you want to see why — it
   leaves its output on screen where the .app has nowhere to put it.)

3. Go to the Settings tab (the gear, top right).

4. Under "Your folders", type the folders where your films and TV live, one
   per line. On a Mac those look like:

       /Volumes/MOVIES AND TV HDD/Films
       /Volumes/MOVIES AND TV HDD/TV Shows

   rather than the D:\Films of a Windows machine.

5. Press SAVE, then press SCAN MY FOLDERS.

Prefer a terminal? "sh run.sh" from inside this folder does the same thing.

WHAT'S IN mac/
  python3/      a self-contained CPython — not installed system-wide, and
                nothing outside this folder is touched
  mpv.app       the official mpv build for Apple Silicon, used for playback
  mpv_config/   mpv's settings, including hardware decoding — see below

HARDWARE DECODING, AND WHY THAT FILE EXISTS
mpv ships with hardware decoding switched OFF. Left alone it decodes video
on the CPU, which on a 4K or HDR file means a hot machine and loud fans for
no reason. mac/mpv_config/mpv.conf turns it on (hwdec=auto-safe), which
hands decoding to VideoToolbox — the media engine on Apple Silicon — and
selects the libplacebo renderer (vo=gpu-next), which here runs on Metal via
Vulkan rather than Apple's deprecated OpenGL.

That config lives in this folder rather than ~/.config/mpv, so it travels
with the folder and doesn't fight any other mpv you install later. Edit it
if you want; the comments explain what each line costs.

A NOTE ON LINUX
The same single Python file runs there too, but the mac/ folder is for
Apple Silicon only. Install python3 and mpv from your package manager, then
"sh run.sh", which builds a small .venv for the one dependency it needs.

The .exe files in this folder are the Windows copies. They are genuinely
ignored on a Mac now — an earlier version would pick mpv.exe up and then
fail to play anything, which is worth knowing if you ever see that.
The Al Jazeera channel needs yt-dlp (brew install yt-dlp) if you want it.


MOVING TO ANOTHER DEVICE
------------------------
This zip is the app, not your library. Your ratings, watch history and
artwork live in files this folder creates when you use it (see YOUR DATA),
and none of them are in the zip - so a fresh copy starts with an empty
library and scans whatever folders you give it.

To take films and shows with you, use the app itself: in the Library, press
SELECT, choose a drive, and every poster shows a blue tick if it's already
on that drive or a red cross if it isn't. Tick what you want and press
ADD TO DRIVE. That
copies them onto the drive as Films\ and TV Shows\ folders, which the app
on the other device can then be pointed at. Nothing on the original machine
is moved or deleted.

Ratings don't travel with the files yet. A library is keyed by file path,
and the same film sits at a different path on every machine.


WHAT'S IN THIS FOLDER
---------------------
  NextUp.exe            the app, for Windows - nothing else to install
  nextup.py             the same app as source, for Mac and Linux
  Next Up.app           double-click this to start it on a Mac
  Next Up.command       the same thing from a terminal, with its output
                        visible — useful when something won't start
  run.sh                starts it on Mac or Linux from a terminal
  mac/                  the Mac runtime: its own Python, mpv, and mpv config
  requirements.txt      the one Python dependency, for Linux
  mpv.exe               the video player it uses (Windows)
  d3dcompiler_43.dll    needed by mpv on some Windows graphics setups
  yt-dlp.exe            only used by the Al Jazeera Live channel (Windows)
  nextup_logo.png       the app's artwork
  nextup.ico            the icon
  nextup_config.json    settings, including the TMDB key
  nextup_fonts\         the app's typefaces, served locally so it looks
                        right offline and from the very first frame
  DEVELOPMENT_NOTES.md  the running log of how it was built, and why

Keep these together in one folder. The app finds mpv and yt-dlp by looking
next to itself, so moving NextUp.exe out on its own will break playback.


WHERE TO PUT IT
---------------
Anywhere you can write to - Desktop, Documents, a folder on any drive.

Do NOT put it in C:\Program Files (or /Applications on a Mac). The app keeps
its database, settings and artwork in its own folder, and those locations
are read-only for normal users, so the first scan would fail.


THE CHANNELS
------------
Twenty-one of them, each looping from a fixed point in time so "what's on"
means the same thing whenever you look. Something is always running on every
one of them. Tune in and it drops you where the schedule has got to, mid-
programme, the way real television does; when something finishes the next
programme follows automatically.

No two channels ever show the same film or the same programme at once.

A card marked JUST ON began in the last ten minutes, so you've missed
nothing worth mentioning.

  1  Everything          everything you own
  2  Universal           family viewing
  3  True Life           documentaries
  4  Action
  5  Comedy
  6  Al Jazeera Live     a live stream (needs the internet)
  7  Saturday Morning    cartoons and adventure
  8  Cult Classic        well regarded but never widely seen
  9  Directors Cut       one director a day
  10 Type Cast           one leading actor, until their films run out
  11 Anime
  12 Binge               shows you rated 7+, six episodes at a time
  13 World Cinema        anything not made in English
  14 Back in Time        history and war
  15 All Day Daytime     reality, daytime and things that are just on
  16 Non-stop Favs       whatever you've hearted
  17 The Watchlist       whatever you've bookmarked
  18 In Black & White    monochrome films
  19 Animated Features   animated films, family or otherwise
  20 Top Shelf           films rated 8.0 and up on TMDB
  21 Cartoon Swim        the late slot - adult animation and Adult Swim

Some fill up as you use the app: Non-stop Favs and The Watchlist need you to
mark things, and All Day Daytime needs the sort of television that's on
while you're doing something else.

SHUFFLE ALL, at the top of the page, redeals every channel at once - a new
running order for each, and each dropped somewhere new in it. Worth pressing
when there's nothing on you fancy, or after you've added a batch of files
and want them in the mix rather than at the back of an order settled months
ago.

A good few channels land at the very start of a programme when you press it,
so there's always a way in - already running, a minute or two along, not
sitting there waiting for you. The rest land anywhere, because a page where
everything just started is a page with nothing to choose between.


YOUR DATA
---------
Once you start using it, this folder will also contain:

  nextup_library.db    your library, ratings, favourites and watch history
  nextup_art/          posters and portraits, so it works offline
  nextup_cache.json    saved lookups, so it doesn't ask the internet twice
  nextup_recs.json     your last set of recommendations
  nextup_resume/       how far into things you got

nextup_library.db is the one that matters. Back that up and you've backed up
your ratings and your watch history. The rest can be rebuilt.


A NOTE ON THE TMDB KEY
----------------------
nextup_config.json contains a TMDB API key so this works out of the box -
it's what fetches posters, genres, cast and plot summaries.

That key belongs to whoever gave you this copy. If you'd rather use your
own, they're free: themoviedb.org > create an account > Settings > API >
request a v3 key, then paste it into the Settings tab.


IF SOMETHING GOES WRONG
-----------------------
Nothing plays
  Settings tab > TEST MPV. It should report a version number. On Windows,
  check mpv.exe is still in the same folder as NextUp.exe. On a Mac, check
  `mpv --version` works in a terminal.

Nothing happens when you double-click it
  It's probably already running - look for the window. If a second copy
  can't start it will tell you why rather than failing silently. On a Mac,
  run "Next Up.command" instead to see the reason on screen.

No posters, no suggestions
  The TMDB key isn't working. Settings tab, paste one in, scan again.

A film has the wrong title
  Open it in the Library and use the correction box on its page. Your fix
  survives every future rescan.

Films are missing after a scan
  If a drive wasn't connected, the app says so and changes nothing. If most
  of the library seems to have vanished it holds the removals back rather
  than acting on them. Reconnect and scan again.

A channel stops after one programme
  Only happens if the player was closed by hand. Tune in again.

The Al Jazeera channel won't start
  That's the only channel needing an internet connection, and the only one
  that uses yt-dlp. Check it's still in the folder (Windows) or installed
  (Mac and Linux).


REMOVING IT
-----------
Delete the folder. Nothing is installed anywhere else, and nothing is
written to the registry.
