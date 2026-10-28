# Changelog

What changed in Next Up, version by version, newest first. Version numbers start at 0.1.1; the work before that is grouped at the end under "Before 0.1".

## 0.2.5 — 2026-10-28

- Fixed: the bar along the top of the window was see-through, so a details page scrolled up under it showed its pictures behind the name and the counts. It wears the page's own background now, looking just as it did, but solid.
- Clicking an episode's code to say "I'm up to here" no longer flashes the screen: the season list updates where it is instead of the show's page closing and opening again.

## 0.2.4 — 2026-10-27

- Ratings, a new place in the Library (the ★ between History and Recommendations), with two halves:
  - **Hall of Fame**: what you've rated, as shelves like the channels. Your top 12, your top TV, the best of each genre, the 2020s back to the classics, world cinema, short and sweet, epics, hidden gems (rated well above TMDB), recently rated, the directors you keep coming back to (the Kubrick shelf) and the actors. Each card shows its first posters, how many and your average; open one for its posters in your order, ranked, twelve at a time, with the year, who made it and when you scored it. Hall of Fame, Rate and All shelves sit on one line with the shelf's name and its line beside it, and stay at the top as you scroll, blending into the page; the Ratings button takes you back to the front. A poster opens its page, where it plays. On the phone, with the PC connected, the PC's ratings.
  - **Rate**: the rating queue, as it was, with how many are left on the switch.
- Rate has left the top menu, which is now Now · Library · Channels.
- **Watch in order**, a switch on each show's page. A show that's one story (Attack on Titan, Arcane) is only ever suggested at the episode you're up to — on Now, Home, the wildcards and the channels — while one you dip into (Seinfeld, Always Sunny) can come up anywhere, as before. Next Up guesses until you set it, from the show's genres and TMDB keywords (sitcom, anthology, miniseries, based on manga), how long it runs, and whether you've watched it in a line or jumped about; the switch says "(guessed)" until you've used it. In-order shows wear a small purple arrow in the corner of their Library poster, and beside the episode you're up to in their season list.
- **Films tags on Now.** Choose Film and a second row of tags opens under the genres: Recent, Classic, Big budget, Low budget, Box office smash, Box office flop, Crowd pleaser, Under the radar, Cult classic, Explosions, Mind-bending, True story, From a book, Part of a series, Not in English, Short and sweet, Epic and Never seen (a film you've rated counts as seen, wherever you watched it). They're worked out from each film's budget, takings, TMDB votes, keywords, year and length, combine with the genres and each other, and one that would leave nothing is greyed. On the PC the alternatives move under the pick, a row of six, while they're up. All of Now's tags sit grey until pressed and then light up solid in their own colour, the genres in the colours they had and each Films tag in one of its own. The genre tags now keep their places as you choose, too: one that would leave nothing greys where it is rather than leaving the row or the others shuffling round.
- Shows any episode of which will do wear a small purple shuffle in that corner instead, so every show says which it is.
- Trophies: a film that tops Hall of Fame shelves has a small gold trophy at the bottom right of its Library tile, with how many: 2001: A Space Odyssey (×4). It stays on top of the hover panel, and hovering it names the shelves. Hidden Gems and Unpopular Opinions count; Recently Rated doesn't.
- A tie in your score on a genre shelf goes to the film that's most that genre — its genre listed first or alone, and that genre's own keywords (parody, mockumentary, slasher, heist...) — so Best Comedies opens with Life of Brian and Borat, not Parasite and Pulp Fiction. TMDB's score only breaks what's left.
- Hall of Fame shelf names in title case (Best Sci-Fi, Short and Sweet).
- Every Hall of Fame shelf now holds at least ten; the shorter ones (most directors' shelves among them) are gone.
- Fixed on Windows: maximising Next Up covered the taskbar. It now fills the screen less the taskbar, and restoring puts it back where it was.
- On a show's page, click an episode's code (S01E02) to say "I'm up to here" — for a show you started somewhere else. The episodes before it count as watched, it becomes the next one, and the purple arrow moves to it.
- Fixed on Windows: a thin grey strip along the top of the window, at any size (the top of the resize frame Windows paints on a window with no title bar). It's gone, and the top edge still resizes.
- Fixed on Windows: maximised, the window left a thin gap round the edge and a grey line along the top (the resize frame), with rounded corners. It now fills the screen to the taskbar, square-cornered; restoring brings the corners and the resize edges back.
- Fixed on Windows: the window couldn't be resized or maximised. Next Up looked for its window by title, and Windows 11 keeps a stand-in window for the taskbar with the same title, which it found first. It now looks only among its own windows.
- The TMDB score is gone from the Now page's card, and from the line above your rating: it swayed the choice more than it should. It still counts in the picking.
- Fixed: a show whose episode stopped under five minutes in (Always Sunny rolling into S05E02 and stopping at 78 seconds) vanished from Continue; it's now offered there as up next, from the start.
- History leaves out anything under two minutes: a start followed within two minutes by anything else (a channel tuned, the next episode), a stop under two minutes in, one that never got two minutes into the programme (dozed off at 78 seconds), and one closed within moments.
- Fixed: Library › Sort › Recently watched counted a few seconds' flick on a channel as watching; it now goes by real sittings, as Continue does.
- Fixed: a show's page stopped drawing its seasons in 0.2.3 (the season the Remote opens it at never reached the part that picks it).

## 0.2.3 — 2026-10-26

- Fixed: shows whose files are numbered in a different order from TMDB's no longer wear other episodes' names, plots and pictures. Futurama's seasons 2–5 (Bender's Big Score showed as Crimes of the Hot), Star Trek: TNG, Cowboy Bebop, Arrested Development, Pokémon, Primal and SpongeBob are put right on the next start; episodes keep your files' order. A file's own title only wins when the rest of the show backs it up, so an odd name alone (Shōgun's first file is called "Crimson Sky") changes nothing.
- The phone's Home fits on the screen: smaller posters, two and a half across, both rows above the now-playing bar. A tap on a poster shows PLAY (HERE / ON PC) and DETAILS over it, and a second tap opens its page, as in the Library.
- Fixed on the phone: Settings › Appearance and Storage no longer run off the side; the Library's Sort and Show are readable again under a full-width search box; the Library's own tabs start with the house right under the word Library.
- Fixed: the phone's Home showed only the phone's own films when the app opened before it had found the PC; it now switches to the PC's library as soon as the PC answers.
- On the phone's Remote, what's playing on the PC opens its page when you tap it: a show at the season you're watching, so you can look along the other episodes, or the film's page.

## 0.2.2 — 2026-10-25

### Headline
- Home: the Library's new front page, where the app opens (the house before Films). Quick Suggest — the better episodes of shows you like and films you love that you haven't seen lately, plus three wildcards. Quick Suggest keeps three lists — Favourites, Deeper cuts and Pot luck — and each visit shows the next one, shuffled, so it doesn't always lean on the top scores. Continue (11 tiles too) is TV and films mixed, newest first; its heading opens History. A tile plays (on the phone, it opens the details). On the PC both rows always fit the window: the tiles are the library's size when there's room and shrink to fit when there isn't.
- Season and episode scores on a show's page: a score on each season tab and each episode, starting from your own rating of the show; a ★ in your accent colour after the show's five best episodes; a mark on unseen ones that should be good. Click a score to rate that episode yourself.
- Click an episode's name for its details: picture, plot, air date, length, TMDB rating, director, writers and guest stars.
- Closing Next Up on the PC hides it in the system tray, so the phone keeps working; click the icon to bring it back, right-click to quit, or switch it off in Settings › Playback.
- The phone's Remote, with nothing playing, is a place to choose: Continue on PC (the last thing, fullscreen), On now (the channels with what's on them), Continue where you left off, and one of tonight's picks. While something plays, Fullscreen also brings the player to the front.

### Also new
- A third look in Settings › Appearance, Silver: Glass's panels in neutral greys over a charcoal background, with the silver accent.
- On the PC's Now page, the small arrow beside Anything shows and hides the genres (pointing right while they're hidden, down while they're out). Anything starts with them folded away; Film and TV bring them out. It used to step back a pick, which BACK on the card still does.
- The PC's Now page sits a little higher with no scroll bar down the right, and the alternatives beside the pick are straight on the page, without the panel or the "Or instead" line.
- Settings › Appearance has a Font choice: Next Up (as it was), Sleek (Manrope) and Cinema (Fraunces headings). All three are bundled, so they work offline.
- A title on the Now page is never cut off: a long one gets smaller and, on the PC, goes onto two lines in the same space, so the buttons stay put.
- The line above the rating on Now says one thing worth knowing, tied to you, rather than a stack of facts: "Kubrick's war comedy. You gave 2001: A Space Odyssey a 9.5.", the one film of a series you haven't seen, a favourite you last watched years ago, one of a show's best episodes you've never seen, or when it'd finish tonight. The film's tagline when there's nothing better.
- Fixed: a film whose folder has the wrong year no longer matches a different film from that year with a similar title ("Rango (2009)" was matching a Spanish film called Mentes enfermas de alto rango, Terminator 2 a making-of). A title that's exactly right now wins even with the year a little out.
- Fixed: flicking through channels no longer fills Continue with films that were only on for seconds (changing channel saved the outgoing film's place, however briefly it was on). Under a minute leaves the place as it was. Starting anything while something else is on (a channel change, Play, next episode) now writes down how far the outgoing one got, so a real stretch on a channel shows in History and Continue, and a few seconds doesn't. Older channel visits are judged by how long they were on before the next thing started.
- The header is back to the page's own colour with a thin line under it, in every look (Glass had a black bar with gold lettering).
- The PC's now-playing bar has its own controls (previous and next episode, play/pause, mute, close the player), and its title opens what's playing.
- On the phone, a second tap on a tile opens its details; with the PC connected, a show or film the phone hasn't got opens the PC's full page, playing HERE or ON PC.
- The phone's Now page is redesigned: a box-sized poster with the facts beside it, everything on one screen, and the same buttons in the same places on every pick (what can't be done greyed out).
- Channels: 2, 4 and 5 (Universal, Action, Comedy) are films only, 3 (True Life) mixes documentary films and series, Non-stop Favs is split into Films and TV (the TV one comes round to the better episodes more often), Al Jazeera moves to the end, Cold Ones is gone.
- The Library's toolbar is one line, Sort then Show then search (the Continue card that sat beside it is on Home now). Its Sort list has Recently watched; with the PC connected the phone's Library opens on Show all, and Show and Sort share one line.
- The show page is wider on the PC: who made it and who's in it down the left, the episodes beside them.
- The Now page's reasons no longer quote ratings; the scores are still on the card.
- The phone's header puts the version left of the camera hole and the counts to its right.

### Fixes and polish
- Quitting Next Up part way through an episode no longer has the next start mark it watched and move Continue on an episode.
- A season added while it was still airing no longer keeps TMDB's placeholder names ("Episode 1") for good: newer and unnamed seasons are checked again on the library scan, at most once a week.
- Anything closed within a minute, or flicked straight past, is no longer recorded: no History entry, no resume point, not counted as recently watched; old entries like that are hidden from History.
- After a restart, the phone's link keeps trying if the previous copy of the app hasn't let go yet.
- The phone finds its camera hole again (it was never told once the page had loaded), and its details pages are solid, with nothing of the Library showing through.
- On the phone, Glass no longer flickers: no blurred page behind, the Now card wears its own poster colours.
- Details windows wait a moment before showing, so a quick one appears whole rather than as "Loading…" for a blink.

## 0.2.1 — 2026-10-21

### Headline
- When the phone can reach the PC, its Now page, Continue row and Channels come from the PC's full library.
- Anything that can play either way offers the choice: ▶ HERE on the phone or ▶ ON PC on the big screen.
- ▶ HERE plays the phone's own copy when it has one, and streams from the PC when it doesn't.

### Also new
- A pick from the PC says so, and Channels says "Asking the PC what's on…" while it works out the schedule.
- A channel watched on the phone moves on to the next programme by itself; stopping it by hand ends it.
- A channel joined from the phone starts at the point the schedule has reached.

### Fixes and polish
- ▶ ON PC on a poster's overlay now responds to a tap; before, the tap went through to the poster.
- Fixed an error that could stop the phone's Now page loading when it first opened.
- ON PC is offered for titles with no TMDB match, and a copy since removed from the phone streams instead.
- A channel started from the phone no longer keeps relaunching itself.
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
- Export your ratings and history as a JSON file from Settings.
- Fix a wrong match from the film page: type the right title and year and it looks it up again straight away, and remembers the fix through rescans.
- Episodes get their real names, descriptions and pictures from TMDB.
- Sorting the Library by Recently added now works for shows, and the Rate queue is shuffled instead of always highest-rated first.
- A now-playing bar on every page, with the channel's name when you're watching one.
- Up Next is renamed Recommendations, and the main tabs have hover hints.
- Folders called "Incomplete…" or "quarantine" are skipped when looking for new files; anything already in the library stays.
- The live news channel finds yt-dlp even if it was installed after Next Up started.
