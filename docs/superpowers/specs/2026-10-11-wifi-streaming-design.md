# Streaming from the PC over home Wi-Fi — design

2026-10-11. Approved in conversation: option A (seamless), cable pairing,
two-way Wi-Fi sync.

## What it's for

On the phone, a film or episode the PC has but the phone doesn't (a greyed
"elsewhere" tile) can be played straight away over the home Wi-Fi, without
copying it first. Away from home, or with the PC off, the app behaves
exactly as it does now.

Success:
- With the PC app running on the same network, a greyed tile lights up and
  PLAY streams it in mpv-android, with seeking and subtitles.
- Watch points and history from a streamed sitting reach the PC on their
  own, without the cable.
- No background polling on the phone. The battery numbers from v0.1.74
  (about 5 app + 0–1 webview CPU-seconds a minute in the background) hold.

Measured on 2026-10-11: a sample of 150 library films averages 5.7 Mbps
(median), 7.7 Mbps (90th percentile) and 13.8 Mbps (heaviest). Any home Wi-Fi
carries that easily, so there's no transcoding: mpv gets the original file.

## What exists already (PC side, v0.1.48)

- `PhoneHandler` on `PHONE_PORT` 8790, off until "Let a phone connect" is on.
  Only the phone's routes exist on it; private and loopback addresses only.
- Pairing: a 4-digit code becomes a `token_urlsafe(32)` token, and only its
  SHA-256 is kept (`phone_cfg()["devices"]`). The phone's device id must be
  16 hex characters, and `sync_device_id()` already is.
- `/phone/hello`, `/phone/snapshot`, `/phone/file?key=` (ranged; 503 for a
  drive that doesn't answer), `/phone/art/…`, GET and POST `/phone/sync`.
- File keys: `m<tmdb>`, `e<tmdb>s<n>e<n>` (`phone_file_key`). A path never
  comes from the phone.
- UDP discovery: `NEXTUP?` on the same port is answered with the PC's name,
  port and version.
- Every route needs `Authorization: Bearer <token>`. mpv-android can't send
  a header, which is the one gap the play links (below) fill.

The phone has none of the client side yet.

## The design

### 1. Pairing over the cable

`usb_send_library` (SEND MY LIBRARY) gains one step after the history swap:

- Turn the phone link on if it's off (`phone_link_set(True)`). This brings
  the one-time Windows Firewall prompt.
- Mint a token for the phone's device id with a new
  `phone_pair_direct(device_id, name)`. It's the tail of
  `phone_pair_finish` without the code: the same id checks (format, not
  another device's id, `known_ids`) and the same storage. The cable is
  proof enough, because a phone on the cable is already trusted with the
  whole catalogue.
- Hand the phone the token, the PC's name, its port, and its addresses
  (`phone_addresses()`) via a new phone route, POST `/api/link/pair`
  (Android only, 127.0.0.1 as all `/api/` routes are).
- The phone keeps them in its config as `pc_link`:
  `{token, pc, port, addresses, last_ip}`.
- Re-sending replaces the token, so a phone that was FORGOTTEN on the PC
  gets back in with the next cable send.
- A link that won't open (port taken) is reported in the send result
  (`streaming: "…"`) and doesn't fail the send.

Code pairing stays in the PC's Settings as it is. There's no pairing screen
on the phone.

### 2. Finding the PC (phone)

`pc_link_check()`:
- Tries `last_ip`, then the stored addresses, with GET `/phone/hello` and a
  1.5 s timeout each.
- Then a UDP broadcast of `NEXTUP?` to 255.255.255.255 on the port, waiting
  up to 1.5 s.
- The first that answers becomes `last_ip`.
- Result: `PC_LINK = {"up": bool, "base": "http://ip:port", "checked": t}`.

When it runs:
- **On app start and on resume** (from `pause_with_app`'s onResume, via a
  page call), in a background thread.
- **Before playing a streamed item**, if the last check is older than 60 s.

It never runs on a timer. An answer of 401 means the token is no longer
valid (forgotten), so it reads as "up: false, needs pairing" and the page
shows nothing more than greyed tiles.

`/api/status` gains `pc_link: {up, pc, needs_pairing}` so the page knows.

### 3. Greyed tiles light up

- While `pc_link.up`, elsewhere films, and elsewhere episodes listed in
  `snapshot_episodes`, are "streamable".
- The tile isn't greyed, and carries a small Wi-Fi mark where the "on this
  device" state would show.
- The peek overlay's PLAY works on them, and so do the details page's
  episode rows.
- "On this device" stays the default shelf and still means files on the
  phone. Show all is where streamable items appear.
- When the PC stops answering (a failed play, or the next check), they go
  grey again.

The library state gets the flag from the server, so the page doesn't work
it out itself: elsewhere rows gain `stream: true` when the link is up.

### 4. Play links (PC)

New on `PhoneHandler`:

- **POST `/phone/play` {key}** (Bearer). It needs the file to exist (the
  same `media_file_check` as `/phone/file`, so a sleeping drive gets 503).
  It returns:
  - `url`: `/phone/stream/<ticket>`
  - `subs`: `[/phone/stream/<ticket>/sub/<n>, …]`, the `.srt`/`.ass` files
    beside the video whose names start with its base name (the
    `subtitle_sidecar` pattern, `<base>.<lang>.srt`, included)
  - `title`
  - `resume`: the PC's own resume position for that file, in seconds
- **GET `/phone/stream/<ticket>`**, and `/sub/<n>`. These need no Bearer
  header, but are still private and loopback addresses only.
  - Ranged, through the same code as `send_media`, refactored to take a
    path.
  - It sends `Content-Type` by extension rather than octet-stream, and
    `inline`, not `attachment`.

Tickets:
- `secrets.token_urlsafe(24)`, held in memory only: `{ticket: (device_id,
  path, last_used)}`.
- A ticket names one file. It expires 12 hours after it was last used, and
  the PC app restarting kills all of them.
- `phone_forget` and turning the link off drop that device's tickets.
- At most 20 live tickets per device; the oldest go first.

### 5. Playing a streamed item (phone)

`/api/play` on Android, for an elsewhere item with the link up:

1. POST `/phone/play` with the key, retrying on 503 every 2 s for up to
   10 s. The page shows "Waking the PC's drive…" meanwhile.
2. The start position is the later of the phone's own last stop event for
   that tmdb identity and the PC's `resume`, unless the user picked "from
   the start".
3. `ANDROID_PLAYER(base + url, start, subs=[base + s, …])`. `open_in_player`
   already passes `filepath` and `subs`; for an http URL it uses
   `Uri.parse` instead of the MediaStore lookup.
4. The sitting is remembered in `_ANDROID_SITTING` as for a local file, but
   with `{"stream": key, "kind", "tmdb_id", "season", "episode"}` instead of
   a local row.

On return, `android_play_finished` logs the same history events (stop with
position, or watched) against the tmdb identity rather than a local row.
History rows already carry `tmdb_id`, and the sync events are built from
those, so they travel the same way.

Audio delay isn't applied, as for local files on the phone.

### 6. Watch points both ways over Wi-Fi

`pc_link_sync()`, run in a background thread after every sitting ends
(streamed or local) and once after a successful start/resume check (at most
once every 10 minutes):

- POST `/phone/sync` with `share_export()["text"]`. The PC's
  `phone_receive` files it, exactly as over the cable.
- GET `/phone/sync`, then `share_import(text, sender=<pc device id from
  hello>)`.

This is the same pair `usb_swap_history` does over the cable, so a phone
synced by either way is in the same state. `/phone/hello` gains `device_id`
(`sync_device_id()`) so the phone files the PC's lines under the same name
the cable swap uses. Failures are quiet and logged; the next sitting tries
again.

### 7. When things go wrong

| Situation | What happens |
|---|---|
| Drive asleep | 503, retried for 10 s with "Waking the PC's drive…"; then "The PC's drive isn't answering". |
| PC goes away mid-film | mpv stops with its own error. Its result gives the position, which is logged. The tile goes grey on the next check. |
| PC app restarted | Old tickets are gone. The next PLAY gets a new one; a film already playing in mpv stops. |
| Phone forgotten on the PC | 401: tiles stay grey. The next cable send pairs it again. |
| NordVPN hides the PC | No answer: tiles stay grey, nothing breaks. Noted in the dev notes as the first thing to check. |
| Different network / away | No answer within ~3 s, all in the background. |

## Security notes

- Play links skip the Bearer token, so their only protection is the
  ticket: 192 random bits, one file, private addresses only, expiring,
  memory-only, and revoked on forget. A ticket in mpv's history on the
  phone is worth nothing after 12 idle hours or a PC restart.
- No new routes on the 127.0.0.1 desktop server face the network. The
  phone's new `/api/link/pair` is on the phone's own loopback server, which
  only the PC reaches, through the adb tunnel.

## Out of scope

- Streaming away from home (over the internet).
- Transcoding.
- Phone-side code pairing.
- Streaming to the S21 and S24 at once is allowed but not tuned.
- Browsing the PC's library beyond what the snapshot already lists: a new
  film on the PC appears on the phone after the next cable send.

## Testing

Automated, `tests/wifi_stream_test.py`, against a real `phone_link_start`
on loopback:
- `phone_pair_direct`: the token works and the id checks hold.
- `/phone/play`: 401 without a token; a ticket for a real key; 404 for an
  unknown key; 503 when `media_file_check` says None.
- `/phone/stream/<ticket>`: plays and ranges; 404 for a bad ticket; a
  ticket for file A can't fetch file B; dropped by forget and by link off;
  expires (clock faked).
- `/sub/<n>`: in range and out of range.
- `pc_link_check`: finds a link by stored address, and by UDP when the
  address is wrong; reads 401 as needs pairing.
- `pc_link_sync`: phone events land on the PC and PC events on the phone,
  and a second run adds nothing.
- Android play path with a fake `ANDROID_PLAYER`: an http URL with subs and
  the right start; the finish logs a stop event on the tmdb identity.

`tests/android_core_test.py` additions:
- The status `pc_link` field.
- Elsewhere rows marked `stream` only while up.

`tests/usb_phone_test.py`: the cable send pairs the phone and reports
`streaming`.

On the S24 with the PC:
- Send the library (pairing).
- Stream a film not on the phone; seek; stop half way.
- Check the watch point on the PC.
- Turn the PC app off: the tile goes grey on the next resume.
