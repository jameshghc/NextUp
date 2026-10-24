# Changelog

What changed in Next Up, version by version, newest first. Version numbers start at 0.1.1; the work before that is grouped at the end under "Before 0.1".

## 0.2.1 — 2026-10-21

### Headline
- When the phone can reach the PC, its Now page, Continue row and Channels come from the PC's full library.
- Anything that can play either way offers the choice: ▶ HERE on the phone or ▶ ON PC on the big screen.
- ▶ HERE plays the phone's own copy when it has one, and streams from the PC when it doesn't.

### Also new
- Closing Next Up on the PC hides it in the system tray instead of quitting, so the phone keeps working; click the icon to bring it back, right-click to quit, or switch it off in Settings › Playback.
- A pick from the PC says so in its label ("Now · from the PC"), and Channels says "Asking the PC what's on…" while it works out the schedule.
- A channel watched on the phone moves on to the next programme by itself; stopping it by hand ends it.
- A channel joined from the phone starts at the point the schedule has reached.
- The phone's Now page is redesigned: a box-sized poster with the facts, genres and why beside it, everything you need on one screen, and the plot and your rating below for whoever scrolls.
- Channels 2 to 5 (Universal, True Life, Action, Comedy) now show films only; Al Jazeera moves to the end of the dial, Cold Ones is gone, and Non-stop Favs is split into Films and TV.
- On the phone, every pick has the same buttons in the same places: HERE and ON PC, then Back, Next and Watchlist, with whatever can't be done greyed out.
- The phone's Remote, with nothing playing, is a place to choose: Continue on PC (the last thing, fullscreen), On now (the channels with what's on them), Continue where you left off, and one of tonight's picks. While something plays there's a Fullscreen button that also brings the player to the front.
- Season and episode scores on a show's page: a score on each season tab and each episode, ★ on the ones you rated highly or keep rewatching, a mark on unseen ones that should be good, and a Best episodes row. The scores start from your own rating of the show, and clicking one lets you rate that episode yourself. Non-stop Favs: TV comes round to the better episodes more often.
- The Now page's reasons no longer quote ratings; the scores are still on the card.
- The Remote shows Continue where you left off: under the message when nothing's playing, under the channels when something is.
- The Library's Sort list has Recently watched: films by when you last played them, shows by their latest episode.
- With the PC connected, the phone's Library opens on Show all, and Show and Sort share one line.
- The phone's Now page is tidier: the chooser sits under Continue, the pick's buttons sit in two fixed rows that don't move, and no scroll bars take up space.

### Fixes and polish
- ▶ ON PC on a poster's overlay now responds to a tap; before, the tap went through to the poster.
- Fixed an error that could stop the phone's Now page loading when it first opened.
- ON PC is offered for titles with no TMDB match, and a copy since removed from the phone streams instead.
- A channel started from the phone no longer keeps relaunching itself.
- Anything closed within a minute, or flicked straight past, is no longer recorded: no History entry, no resume point, and it doesn't count as recently watched. Old entries like that are hidden from History too.
- After a restart, the phone's link keeps trying if the previous copy of the app hasn't let go yet.
- A stray code showing instead of an apostrophe is fixed.

## 0.2.0 — 2026-10-20

### Headline
- The phone works as a remote for the PC: a Remote tab appears whenever the PC is reachable.
- The Remote has play/pause, a seek bar, back 10 s and forward 30 s, volume, mute, audio delay, subtitles (cycle and FIND), audio track, previous/next episode, skip, the six channel presets and STOP.
- ▶ ON PC on any poster or episode starts it on the big screen; for a show it picks the next episode.
- "Are you still watching?" can be answered from the phone.
- A now-playing strip sits on the phone's other screens; tap it to open the Remote.

### Also new
- The Remote fits on one screen with no scrolling, has thumb-sized buttons, and splits into two columns in landscape.
- The Glass look is available on the phone too.
- The Remote only checks in with the PC while you're looking at it, to save battery.
- A friendlier first run: SCAN saves the folders you typed, mpv is found straight after installing it, an empty library isn't asked about OneDrive, and the scan summary is clearer.
- A new step-by-step guide for people setting Next Up up for the first time.

### Fixes and polish
- In portrait, the phone's header runs round the camera hole instead of under it.
- Working buttons no longer look disabled in the Classic style.
- In a narrow window the pick now comes before the chooser.
- Settings that only apply to the PC are hidden on the phone.
- A film you've barely begun says "only just started" rather than "0% through".
- Seeking from the Remote reports where it landed, a slow PC isn't mistaken for a missing one, and the phone stops asking once the PC goes away.
- ON PC brings the player to the front, and the now-playing strip no longer covers the last row of posters.

## 0.1.81 — 2026-10-20
- The current pick's artwork only tints the Now page; the Library and the other tabs stay a neutral glass.

## 0.1.80 — 2026-10-19
- The pick's buttons stay in exactly the same place from one pick to the next.
- A long title shrinks to fit one line, and only past that ends in "…" with the full title on hover.
- The line under the title and the "why" always take the same room, and Play is the same width whether it says Play or Resume.

## 0.1.79 — 2026-10-19
- Glass is darker, so bright artwork (The Simpsons, The White Lotus) no longer lights up the page.
- A solid black title bar with NEXT UP in the accent colour.
- BACK now sits beside NEXT on the pick card.
- NEXT, BACK, WATCHLIST and favourite have a fill and outline in Glass, so they don't fade into the background, and stay visible when disabled.

## 0.1.78 — 2026-10-19
- Glass no longer puts a white sheen over the Now page.
- The tag chooser floats without a box, and starts level with the Continue cards (or at the top when there's nothing to continue).

## 0.1.77 — 2026-10-19
- New Glass style: frosted panels with the current pick's poster washed out behind the page. It's the PC's default; the phone starts on Classic to save battery.
- Settings → Appearance: Classic or Glass, accent colour (eight choices), glass strength, background art, corners, and RESET.
- The accent colour now reaches everything that used to be fixed marigold.
- Changes preview live, and the page opens in your chosen look with no flash of the old one.
- Panels never get so clear that buttons are lost over bright artwork.

## 0.1.76 — 2026-10-19

### Headline
- "Are you still watching?" now asks in the middle of a film too: it pauses, and if nobody answers it rewinds ten minutes before closing, so you can find your place.
- The Now page's Continue row has films again: newest first, films and TV mixed, up to 24.
- Settings is split into tabs (Library, Playback, Phone & sharing, Storage), and remembers the last one you used.

### Also new
- On the PC the chooser moves to the top right, and the mouse wheel scrolls Continue sideways.
- Making a choice keeps the chooser where it was on screen; on the phone the page no longer jumps to the top.
- "Anything" is chosen from the start with every tag showing, and tags combine under Anything too.
- Chosen tags are underlined as well as filled.

### Fixes and polish
- If mpv's saved-places folder goes missing or can't be read, Next Up leaves your watch points alone instead of treating everything as finished.

## 0.1.75 — 2026-10-11

### Headline
- Stream from the PC over home Wi-Fi: greyed titles on the phone light up in colour, with a Wi-Fi mark, whenever the PC is reachable.
- They play in mpv on the phone with nothing copied, subtitles included.
- Playback starts from wherever you stopped last, on either device.

### Also new
- SEND MY LIBRARY over the cable now also pairs the phone for Wi-Fi.
- The phone finds the PC by itself when the app opens or comes back to the front.
- History swaps both ways over Wi-Fi after every sitting.
- A greyed show opens an episode list with PLAY or RESUME on each episode and a tick for those watched.
- "Waking the PC's drive…" shows while a sleeping drive spins up.
- A film streamed part way and later copied to the phone starts where you left off.

### Fixes and polish
- A stream cut off part way isn't counted as watched.
- A PC that's slow to answer still lights up the tiles, and problems are shown on screen.

## 0.1.74 — 2026-10-10
- The phone app stops waking itself in the background, which saves battery; it answers straight away when you come back to it.

## 0.1.73 — 2026-10-10
- Genres combine: pick several at once and the suggestion has all of them.
- Genres that can't produce anything with your current choice are greyed out.
- On the PC the chooser moves to the right-hand column, so the pick sits higher.
- NOT THIS is now called NEXT.

## 0.1.72 — 2026-10-10
- The PC's Now page is rebuilt on the phone's ideas: Continue along the top, a one-line chooser, then the pick with "Or instead" alternatives beside it.
- The Mood, Format and Genre boxes and the reason cards are gone.
- The pick card reads in a new order: what it is and why, PLAY, the facts, a three-line plot (click for the rest), a short why, then your rating.
- Six alternatives are shown, and in a narrow window they move under the pick.

## 0.1.71 — 2026-10-10
- On the phone, the WHY THIS? button and its cards are gone; a short "why" now sits inside the pick card.
- The "best-rated in your library" reason no longer says "and and", and mentions your own rating when you've given one.

## 0.1.70 — 2026-10-10
- The phone gets a step-by-step chooser: Anything, Film or TV, then genres in their own colours.
- "Or instead" posters appear right under the phone's suggestion.
- The phone's Continue tiles are a third smaller.
- The heart and bookmark on a poster's overlay sit in the corners where their marks normally show.
- TV genres such as "Action & Adventure" no longer show up as a second Action.

## 0.1.69 — 2026-10-10
- Titles that are only on the PC can be favourited or watchlisted from the phone, and the PC picks it up at the next swap.

## 0.1.68 — 2026-10-10
- The phone's Now tab is rebuilt for the small screen: Continue first, then the pick with a full-width poster and PLAY within reach, then the filters folded into one line.
- Swipe left on the pick for the next one; tap the poster to open its page.
- Narrower margins on the phone, so there's more room on every tab.
- Favourites on the phone shows every favourite, whether or not it's on the phone.

## 0.1.67 — 2026-10-10
- Favourites and the watchlist travel to the phone with the library, including titles the phone doesn't have.
- Films and shows on the phone take the PC's favourite and watchlist marks where they have none of their own.

## 0.1.66 — 2026-10-10

### Headline
- Recommendations gets a home page of rows: Finish what you have, Films for you, Shows for you, subjects you like, and people (directors and actors).
- REFRESH deals a new hand of picks without going back online.
- Tap a pick for a details page with the plot, cast, why it's there and NOT FOR ME — HIDE.

### Also new
- A quiet library check at start-up, which refreshes suggestions in the background when files have changed or they're over a week old.
- SEE ALL opens the old full page, or a subject's whole list.

## 0.1.65 — 2026-10-10
- The duplicate X-Men '97 tile is merged into one, for good.
- Shows that match the same TMDB title are merged automatically, keeping ratings, favourites and history.
- The same episode found in two different folders is treated as one copy, keeping the later watch point.
- Show names that differ only in punctuation are now recognised as the same show.

## 0.1.64 — 2026-10-09
- History, ratings, favourites and watch points now swap between the phone and the PC over the cable, as part of SEND MY LIBRARY.
- The phone takes its name from Android (e.g. "James's S24 Ultra") instead of "localhost".
- An older phone app gets a polite "update Next Up on the phone" message rather than an error.

## 0.1.63 — 2026-10-09
- Fixed the phone forgetting every film's watch point after a restart; the lost points were rebuilt once from your history.
- The phone's library opens on "On this device", with Show all a tap away.
- In portrait the page starts below the camera.

## 0.1.62 — 2026-10-09
- Copies to the phone show their progress as they go, instead of sitting at 0%.
- CANCEL stops a copy part way through a film, and closing Next Up stops it too.
- A copy that was cut off just before finishing is completed rather than sent again.

## 0.1.61 — 2026-10-09
- Fill a drive straight from the Library: a tick button opens an add bar with the destination and free space, and a floating ADD button shows the total.
- WHAT'S ON IT shows a drive's contents inside the Library screen, searchable and filterable.
- The separate Drives tab is gone, with nothing lost.

## 0.1.60 — 2026-10-09
- Every poster's peek on the phone shows three coloured tags: genres, then what the title is like, then the decade.
- The TMDB score is gone from the phone peek (your own rating stays), and DETAILS is underlined.

## 0.1.59 — 2026-10-09
- The phone's poster peek is redesigned: name and year, length, colour-coded genres, scores, PLAY, and a DETAILS button under it.
- A second tap on the poster closes the peek.
- No blue flash when tapping.

## 0.1.58 — 2026-10-09
- Tapping a poster on the phone shows its key facts and a PLAY button (RESUME or CARRY ON where it applies); a second tap opens the details.

## 0.1.57 — 2026-10-09
- The library works on a phone held sideways: six posters across, with the page scrolling as one.
- Poster names are centred on the phone, and the "on <PC>" strip no longer covers the year.

## 0.1.56 — 2026-10-09
- The phone app is full screen, keeping the navigation buttons in portrait and hiding them in landscape.
- Back closes whatever is open before leaving the app.
- Swipe down to close a details page; the header no longer covers it.

## 0.1.55 — 2026-10-09
- Audio delay is remembered for each film and episode and put back whenever it plays.
- A delay set for one episode no longer follows you into the next file.
- A film played to the end in the phone's mpv now counts as watched.

## 0.1.54 — 2026-10-09
- The phone remembers where you stopped and resumes from there.
- Your PC ratings show on the films stored on the phone.

## 0.1.53 — 2026-10-08
- The copy tray lists every ticked title with its size, and the total against free space turns red when it won't fit.
- The phone plays films in the mpv app (or offers Android's "Play with" list if it isn't installed).
- The Android app has the Next Up icon.

## 0.1.52 — 2026-10-08
- Library › Drives is now the one place to fill a drive: tap posters to add them, with marks for what's already there, and a tray that prices and runs the copy.
- The Settings docking card and the Library's SELECT mode are gone, as they did the same job.
- REREAD also finds drives and phones plugged in since the page opened.

## 0.1.51 — 2026-10-08
- A phone on the cable appears as a drive you can copy films and shows to.
- After copying, the phone rescans and the copied titles turn from grey to colour.

## 0.1.50 — 2026-10-08
- The PC sees a phone plugged in by cable, and SEND MY LIBRARY gives it your whole catalogue and posters (never video files).
- Titles not on the phone show greyed, labelled with the PC that has them.
- The Show list is simplified to Show all, Part way through, Watchlist and On this device.
- A first phone layout: tabs above the Library rows, and film and show pages in one column.
- The phone uses its "Film & TV" folder, with dark status and navigation bars.
- Fixed switching shelves quickly sometimes showing the wrong posters.

## 0.1.49 — 2026-10-08
- Next Up runs on Android: the first version of the phone app, with every tab working and films found on the phone.

## 0.1.48 — 2026-10-07
- The PC can let a phone connect over home Wi-Fi (Settings → Your phone), groundwork for the phone app.
- Pairing uses a code that lasts five minutes, works on the home network only, and the phone finds the PC without typing an address.
- Fixed before release: file names with accents or curly quotes, phones taking another device's identity, and connections that carried on after the link was turned off.

## 0.1.47 — 2026-10-03
- New channel, Cold Ones #22: random videos from the YouTube channel on a loop, refreshed daily, with Shorts and live streams left out.
- If YouTube refuses to play, the channel stops and says yt-dlp needs updating, rather than racing through every video.

## 0.1.46 — 2026-10-03
- The Library's places move back onto the same line as the shelves, still clearly separate, shrinking to icons on narrower windows.

## 0.1.45 — 2026-10-03
- The Library splits into shelves (Films, TV Shows, Favourites) and places (History, Recommendations, Drives), each with its own row.

## 0.1.44 — 2026-10-02
- Downloads that arrive as a single file, not in a folder, are now sorted and listed as waiting.
- Empty show tiles left behind after sorting disappear, unless you've rated, favourited or watched them.

## 0.1.43 — 2026-09-28
- A design pass on Settings: matching headings, consistent SAVE buttons, tidier rows that lay out cleanly at any width.
- The docking station's selection count no longer disappears on narrower windows.

## 0.1.42 — 2026-09-25
- Every film and show now quietly gets a watch score based on how much you've actually watched, ready for future features. Nothing shows it yet.

## 0.1.41 — 2026-09-25
- The missing-episodes list updates as soon as you add episodes, without waiting for a new scan.

## 0.1.40 — 2026-09-25
- Continue follows the episode you watched most recently, not the one furthest along; finish one and it moves on to the next.
- Favourite shows are offered on the Now page as a random episode, then play on in order.
- The Continue tile shows the "up next" episode after one you've finished.
- Seinfeld and six other shows that had quietly stopped being suggested are back.

## 0.1.39 — 2026-09-24
- When sorting downloads, the better copy of a film or episode is kept, judged by resolution first.
- An upgraded copy takes over your old file's name, keeping its rating and history.
- The losing copy is set aside rather than deleted, and Settings asks what to do with it: MOVE TO BIN, SHOW FOLDER or NOT NOW.
- A film you already have in another format is spotted, and the preview warns about duplicates before anything moves.

## 0.1.38 — 2026-09-23
- The Rate card has the film's backdrop behind it, with the next card's pictures loaded ahead.
- Fixed rating a card silently skipping the next one.
- Every Rate card is the same height, so the buttons don't move.
- The full description and the film's tagline are shown.

## 0.1.37 — 2026-09-23
- The TMDB score is removed from the Rate tab, so it doesn't sway your own rating.

## 0.1.36 — 2026-09-23
- Fixed the Favourites and Watchlist shelves showing the whole library.
- The Favourites tab shows films and shows together.

## 0.1.35 — 2026-09-23
- The "continue where you left off" tile shows your latest film on Films and your latest show on TV Shows.

## 0.1.34 — 2026-09-22
- "Are you still watching?" after midnight now waits 90 minutes by default, not 45, so long episodes aren't interrupted every time.

## 0.1.33 — 2026-09-22
- "Are you still watching?": when episodes, the queue or a channel would carry on by themselves, Next Up asks first.
- It asks between programmes, never over one, with a different wait for daytime, evening and after midnight (all adjustable).
- The question shows in the player and in the app; with no answer after five minutes the player closes so the PC can sleep.
- Pressing anything in the app or using the player's keys counts as being there.

## 0.1.32 — 2026-09-20
- History opens on the last week, with buttons to look further back.
- Pressing the tab you're already on takes you back to its start: the Library to Films, page one; Channels and Rate reload. The Now page keeps its pick.

## 0.1.31 — 2026-09-20
- A button in Settings sorts new downloads into your Films and TV folders, always showing a preview first.
- Episode titles are filled in from TMDB as files are sorted.
- The downloads folder can be chosen, and Next Up suggests one.

## 0.1.30 — 2026-09-20
- Whether the queue panel is tucked away is now remembered between restarts.
- About 600 MB of unused browser files were cleared out.

## 0.1.29 — 2026-09-20
- Behind-the-scenes tidy-up; nothing changes in how the app works.

## 0.1.28 — 2026-09-20
- Next Up can be started again straight after closing it, without a "port in use" error.
- Closing is quicker, as the artwork cache is only saved when it has changed.
- Starting a new copy while the old one is still closing waits a few seconds instead of failing.

## 0.1.27 — 2026-09-20
- Pick something is fairer: highly rated titles no longer take most of the picks, and far more of the library gets offered.
- Shows you're in the middle of are offered properly; they had been almost impossible to get.
- Shows you've been watching lately get a boost, and the card says so (e.g. "64 episodes in the last 90 days").
- A show you're bingeing can't take over: the whole show is held back for a while after it's offered.

## 0.1.26
- The grey hints were removed from the right-click menu. (No notes survive for this version; this is the only change mentioned later.)

## 0.1.25 — 2026-09-18

### Headline
- Right-click any poster for Play, Play next, Add to queue, favourite, watchlist and Open.
- A queue panel down the side of the window, docked, overlaid or tucked away, saved between sessions.
- The queue moves on only when something finishes, never when you close the player.

### Also new
- Queueing a show adds the episode you're up to, and queueing it again adds the one after.
- The remote's SKIP moves to the next item in the queue; channels keep their own schedule and ignore it.
- The next pick on the Now page is prepared in advance, so its picture appears instantly.

## 0.1.24 — 2026-09-17
- Recommendations: "Shows you might like", based on the shows you rate and favourite.
- Recommendations: "What would fill your channels", leading with channels that would repeat within a day.
- The Recommendations page is more compact, with a single row of counters.
- Cards show the genre, a TV flag where films and shows mix, and for shows the creator and number of seasons.

## 0.1.23 — 2026-09-14
- The header gives back a row: the version and counts move into the title bar, and the Library's section tabs share the main tabs' line.

## 0.1.22 — 2026-09-14
- History, ratings, the watchlist and favourites are shared between your computers through a OneDrive folder, with no account needed.
- Where you stopped on one computer carries on from there on the other.
- History shows which computer each evening was watched on.
- When two computers disagree, the later change wins; Settings warns if OneDrive isn't running.
- History now always lists the newest sittings first.

## 0.1.21 — 2026-09-14
Includes the Mac work of 13 September, brought home to Windows.

### Headline
- Next Up runs on a Mac as a proper app, with its own icon and a built-in player with hardware decoding.
- A "who's watching" screen to pick a profile, and a name for each computer.
- A computer can show another machine's library, greyed and labelled with where it lives.

### Also new
- History groups each title into one row, with every sitting inside it, plus RESUME or WATCH AGAIN and OPEN buttons.
- Sittings cut short when the app was closed now show in History.
- A duplicates finder: films you hold twice, a recommendation of which copy to keep, and MOVE TO BIN (to the Recycle Bin, never straight deletion).
- Every duplicate row says clearly whether it is kept or goes.
- The Library's header is more compact, so posters start higher up the window.

### Fixes and polish
- Closing the app now stops the player and saves where you were.
- Closing the main window also closes the remote.
- Seinfeld's final episodes, named differently, no longer appear as films.
- Channels no longer stop after one programme.

## 0.1.20 — 2026-09-13
- In SELECT mode every poster shows whether it's on the chosen drive: a blue tick, a red cross, or a count for shows partly there.
- The marks, the price and the copy all agree, so nothing ticked is ever copied twice.
- Disabled buttons now look disabled.

## 0.1.19 — 2026-09-13
- A Drives section in the Library to browse what's on a plugged-in drive, with a switch for "only what isn't in my library".
- Much better matching of a drive's files to your library, even when they're named differently.
- The copy tray no longer lingers over History or Recommendations.

## 0.1.18 — 2026-09-13
- Films already on a drive are recognised wherever they sit on it, not just where Next Up would have put them; the poster says where.

## 0.1.17 — 2026-09-13
- Drop-down lists are dark again instead of white.
- Posters show ON DRIVE (or how many episodes are there) once a drive is chosen, and the copy price skips what's already on it.

## 0.1.16 — 2026-09-13
- SELECT mode in the Library: tick posters and ADD TO DRIVE, with the size shown to confirm before copying.

## 0.1.15 — 2026-09-13
- A facelift: each film's backdrop now fills the space behind the Now pick and the detail pages.
- Outlines replaced with soft shading and shadows, consistent rounded buttons and inputs, and a switch-style tab bar.
- Each channel card carries a faint tint of its own colour.

## 0.1.14 — 2026-09-08
- On the Rate tab you can open any title from its poster, its name or the top-ten lists.
- Play buttons there too, naming the episode for a show (e.g. PLAY S09E15).

## 0.1.13 — 2026-09-08
- Saturday Morning is now a hand-picked children's line-up, no longer full of adult comedies.
- Titles typed with or without accents (Pokémon / Pokemon) now match.

## 0.1.12 — 2026-08-24
- A docking station in Settings: tick films and shows and copy them to a USB drive, ready for another player.
- It shows the size against free space before starting, a progress bar while copying, and can be cancelled safely.

## 0.1.11 — 2026-08-17
- A watchlist button on the Now card; on an episode it adds the whole show.

## 0.1.10 — 2026-08-17
- History measures how much of a film you actually got through, not how long the player was open (no more eight hours of a film you fell asleep to).
- Every History row shows a percentage, and older rows now count towards the totals.

## 0.1.9 — 2026-08-17
- Channels are always running, so you drop into the middle of something; the half-hour start times from 0.1.8 are gone.
- SHUFFLE ALL now puts several channels just a couple of minutes into something.
- The same show never plays on two channels at once.
- A watch history in the Library, grouped by day, including programmes you stopped part way.
- The Now page won't suggest a film you watched most of in the last month.

## 0.1.8 — 2026-08-17
- Three new channels: Animated Features #19, Top Shelf #20 and Cartoon Swim #21.
- SHUFFLE ALL gives every channel a new running order.
- A year-range slider for the "For you" recommendations.
- Channels started programmes on the half hour (withdrawn the same day in 0.1.9).

## 0.1.7 — 2026-08-16
- Pick something is far more varied: the watchlist no longer takes over, much more of the library is in the draw, one pick in four is completely random, and nothing repeats within 150 picks.

## 0.1.6 — 2026-08-16
- The Now page no longer jumps when you press Pick something.

## 0.1.5 — 2026-08-15
- Recommendations becomes a shelf in the Library, and remembers its results between restarts ("Last looked today").
- Settings is now a gear icon.

## 0.1.4 — 2026-08-09
- The Now page remembers what it has offered, even across restarts, so the same films don't keep coming back.
- A BACK button returns to a pick you skipped past.

## 0.1.3 — 2026-08-09
- A "Continue where you left off" row at the top of the Library, newest first.
- Resume buttons now really resume, including on the Now page and the film page.

## 0.1.2 — 2026-08-08
- A darker, true-black look with softer lifting and motion.
- Fonts are built in, so the app looks right from the first moment and offline.
- A drive that has gone to sleep gives a clear message instead of freezing the app.

## 0.1.1 — 2026-08-05
Also covers the unnumbered work of 6–7 August.

### Headline
- Playback rebuilt: the next title loads in the same player window, with a live progress bar, and finishing something is now recorded.
- Channels move on by themselves when a programme ends, and start each programme at the right point.
- Six new channels: World Cinema, Back in Time, Trash TV (later All Day Daytime), Non-stop Favs, The Watchlist and In Black & White.
- Favourites: mark any film or show, with its own Library section, its own channel and richer pages, plus pages for actors and directors.
- A remote control window that stays above the player: channels, volume, pause, skip, presets, subtitles, audio track, audio delay and episodes.

### Also new
- Fetch subtitles from OpenSubtitles straight from the remote.
- Recommendations survive a restart, learn your taste better, and can be sorted by match, rating or year.
- Posters are stored locally, so the library works offline.
- A frameless window with its own title bar and no console window.
- Show pages open one season at a time, starting at the season you're on.
- A refresh button in the Library to rescan your folders.
- Channel cards are all the same size, each with its own colour, and named like "Directors Cut #9".
- Directors Cut and Type Cast play films in release order, and Type Cast stays with each actor for their whole run of films.
- Binge blocks are six episodes instead of three.
- A self-contained Windows package with everything it needs.

### Fixes and polish
- An unplugged drive is no longer read as empty, and Next Up won't remove more than half the library at once.
- A change of media folder no longer duplicates the whole library.
- Better handling of oddly named files, specials and extras folders.
- Fixed the app freezing when the remote was opened.
- The mouse wheel scrolls from anywhere on the page.
- Live channels reuse the open player window.

## Before 0.1 — 2026-08-04
Early work, before the version numbers were reset to 0.1.

- Channels, built from scratch: twelve of them, from Everything to Binge, plus a live news channel, all on a fixed schedule so "what's on" is always the same.
- A Watchlist, with its own Library filter and a nudge in the evening's picks.
- Film pages with the full plot, tagline, cast and director, and similar films from your own shelf.
- An Actors section in Recommendations.
- The evening's picks are no longer almost all TV, and well-rated films come back as rewatches.
- Many library fixes: duplicate per-season shows merged, lettered episodes recognised, and missing episode lengths and show cast filled in.
- Starting something new closes the old player politely, so its place is saved.
- A paged Library, half-star ratings, and the Next Up logo as the app icon.
