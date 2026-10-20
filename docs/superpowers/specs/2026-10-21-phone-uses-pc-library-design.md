# The phone draws on the PC's library — design

2026-10-21. Decided with the user:
- **Now, Continue and Channels** draw on the PC while it's reachable.
- **Where a title can play both ways, the user gets the choice:** ▶ HERE
  and ▶ ON PC side by side, no default.
- **Dropped:** the "PLAY asks where?" dialogue for everything else.

## What it's for

With the phone and PC on the same Wi-Fi, the phone's Now page and Channels
behave as if the whole PC library were on the phone. Away from the PC they
use the phone's own library, exactly as today.

Success:
- **Now:** with the PC up, the pick, the "or instead" alternatives and the
  genre chooser cover everything on the PC.
- **Continue:** shows what you're part way through on either device.
- **Channels:** the phone's Channels tab shows the PC's channels with what's
  on now. Each can be watched here (from the current point) or on the PC.
- **The choice:** a title that can play both ways shows ▶ HERE and ▶ ON PC.
  One that can only play one way shows just that button.
- **Away from the PC:** everything is as today, and nothing errors.
- **Battery:** no new polling. Pages ask the PC when opened or refreshed,
  as Now already does.

## Approach: ask the PC

The PC already has the full library, the picking logic (`build_tonight`,
`available_genres`), Continue (`build_continue`) and the channel schedule
(`resolve_all_channels_now`). It also has the phone's history, swapped over
Wi-Fi after every sitting. So rather than teach the phone's library about
the PC's titles, the phone asks the PC for these lists while it's reachable,
and plays what comes back:
- **here:** a local file if the phone has one, otherwise streamed
  (`pc_stream_play`);
- **on the PC:** `/phone/remote/play`, or tuning a channel.

The alternative was folding the PC's titles into the phone's own library
so every feature sees them. It was rejected: it touches every code path
that assumes a local file, for no gain over asking the PC.

## Design

### 1. PC: three read-only routes on `PhoneHandler`

All Bearer-gated and home-network only, as every phone route is.
- **GET `/phone/now?kind&mood&genre&exclude&count`:** `build_tonight(...)`
  with the same arguments as `/api/tonight`, plus `continue`
  (`build_continue()`).
  - Each item gains `ident`, `{kind: "movie"|"episode", tmdb, season?,
    episode?}`, so the phone can stream it or ask the PC to play it.
    Items with no tmdb id get no `ident`, and the phone shows them as ON PC
    only.
  - Art is rewritten to `/phone/art/<name>`.
- **GET `/phone/genres?kind&with`:** `available_genres`.
- **GET `/phone/channels`:** for each channel:
  - id, name, live flag;
  - now: title, sub, art, `ident`, `offset` seconds into it, `duration`;
  - next: title.
  - Live and YouTube channels have no `ident`, so they're ON PC only.

### 2. Phone: passthrough and play-here

- **`/api/pcnow`, `/api/pcgenres` and `/api/pcchannels`:** passed through
  `pc_link_call`. Art goes via `/api/pcremote/art/`. When the PC is away,
  `{error: PC_AWAY}`.
- **`/api/play` with `{stream: ident, start?}`** (exists). Two additions:
  - When the phone has that title locally (a tmdb match), it plays the
    local file, not a stream.
  - An explicit `start` (seconds), for a channel's current point.
- **Watching a channel here.** The phone plays the programme from
  `offset`. When it plays to its end, the phone asks `/phone/channels`
  again and plays what's on that channel now, so the channel carries on.
  Stopping by hand ends it. One channel sitting at a time.

### 3. Phone: the page

- **Now.** While `pcLinkUp`, `loadTonight` and the chooser's genre counts
  use `/api/pcnow` and `/api/pcgenres`; otherwise `/api/tonight`, as
  today.
  - The pick card's PLAY row becomes ▶ HERE and ▶ ON PC when both apply,
    with NEXT, BACK and WATCHLIST unchanged.
  - The alternatives and Continue cards get the same pair, smaller.
  - A small "From the PC's library" line under the chooser says where the
    picks come from.
- **Channels.** While `pcLinkUp`, the tab lists the PC's channels: name,
  what's on (art, title, how far in) and what's next, each with ▶ HERE
  (when it has an `ident`) and ▶ ON PC. Otherwise it's the phone's own
  channels, as today.
- **ON PC** goes through `/api/pcremote/play`, or the remote's `channel`
  action, and opens the Remote, as now.

### 4. Errors

| Situation | What happens |
|---|---|
| PC goes away mid-browse | The next load falls back to the phone's own lists. A press on HERE (stream) or ON PC says "The PC isn't on the Wi-Fi right now." |
| Title has no tmdb id | ON PC only. |
| Channel is live or YouTube | ON PC only. |
| A drive asleep for HERE | The existing "Waking the PC's drive…" retry. |

## Out of scope

- Recommendations and Rate drawing on the PC.
- Queue management from the phone.
- Channel auto-continue when the PC goes away mid-channel: the sitting just
  ends.

## Testing

- **`tests/phone_pclib_test.py`,** against a loopback PC link as in
  `phone_remote_test`:
  - `/phone/now` gives picks with `ident` and phone-fetchable art, and
    honours `kind` and `genre`;
  - `/phone/genres` matches `available_genres`;
  - `/phone/channels` gives `offset`, `ident` and no `ident` for live
    channels;
  - the phone passthroughs, and their copy with the PC away;
  - `/api/play` with a stream ident the phone has locally plays the local
    file;
  - an explicit `start` is honoured;
  - a channel sitting that ends plays the channel's next item; one stopped
    by hand doesn't.
- **Page source checks:** Now uses the PC routes only while `pcLinkUp`;
  the HERE / ON PC pair; Channels.
- **In `phone_serve.py --with-pc`** with the fake mpv, then on the S21.
