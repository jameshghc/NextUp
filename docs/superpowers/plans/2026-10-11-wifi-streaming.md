# Streaming from the PC over home Wi-Fi — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** On the phone, a greyed "elsewhere" film or episode plays straight
from the PC over home Wi-Fi, and history goes both ways over Wi-Fi after
each sitting.

**Architecture:** The PC's existing phone link (`PhoneHandler`, port 8790)
gains play tickets: unguessable URLs for one file that mpv-android can open
without a header. The phone, which is the same `nextup.py` with
`PLATFORM == "android"`, gains a small client:
- find the PC (stored address, then UDP `NEXTUP?`)
- ask for a ticket and hand the URL to mpv
- swap history with the existing `/phone/sync` routes

Pairing happens during the cable's SEND MY LIBRARY.

**Tech Stack:** Python stdlib only (http.server, urllib, socket, sqlite3),
the embedded page JS, and Chaquopy/toga on the phone (`android/src/mobile/app.py`).

**Spec:** `docs/superpowers/specs/2026-10-11-wifi-streaming-design.md`

## Global Constraints

- **One file.** All app code goes in `nextup.py`. Only intent building goes
  in `android/src/mobile/app.py`.
- **Line endings.** LF only. Write patches with Python scripts in the
  scratchpad, not heredocs with backslashes.
- **No background timers on the phone.** Link checks run on page load, on
  `visibilitychange` to visible, and before a play. Wi-Fi sync runs after
  a sitting, and after a successful check at most every 600 s.
- **Network limits.** Play and stream routes answer private and loopback
  addresses only, the same as `PhoneHandler.from_home`. A path never
  comes from the phone; only file keys do (`m<tmdb>`, `e<tmdb>s<n>e<n>`).
- **Tickets:**
  - `secrets.token_urlsafe(24)`, held in memory only
  - one file each
  - expire 12 h (43200 s) after last use
  - at most 20 live per device, oldest dropped first
  - dropped by `phone_forget` and by turning the link off
- **Phone timeouts and retries:**
  - each address `/phone/hello`: 1.5 s
  - UDP wait: 1.5 s
  - a 503 from `/phone/play`: retried every 2 s for up to 10 s
- **Copy:**
  - "Waking the PC's drive…"
  - "The PC's drive isn't answering"
  - Code comments and dev notes keep the project's plain explanatory voice.
- **Tests and version.** Tests use the `check()` script style of
  `tests/phone_link_test.py`, sandboxed with `devserve.isolate`, and are
  added to `tests/run_all.py`. The version goes to `0.1.75` in
  `nextup.py` and `android/pyproject.toml`.

## Review Focus

1. **A file name outside Latin-1** ("Don’t Look Up – 2021") must still
   stream: the headers use the RFC 5987 form. Test in Task 1.
2. **mpv seeks to the last byte.** Ranges like `bytes=<size-1>-`, and a
   start past the end giving 416. Test in Task 1.
3. **A PC with several adapters** (NordVPN's included): stored addresses are
   tried in order and the one that answered first is remembered as
   `last_ip`. Test in Task 3 (a dead first address).
4. **An elsewhere episode the PC doesn't have** (the show is in the
   snapshot, the episode isn't in `snapshot_episodes`): not streamable, and
   `/phone/play` returns 404. Tests in Tasks 1 and 5.
5. **Streamed, then copied to the phone later:** the watch point carries
   over, because it's on the tmdb identity in history. Test in Task 5.

---

### Task 1: Play tickets on the PC

**Files:**
- Modify: `nextup.py`:
  - `PhoneHandler.send_media` (~12249) becomes `send_path`
  - `PhoneHandler.do_GET` and `do_POST`
  - `phone_forget` (~11977) and `phone_link_stop` (~12532)
- Test: `tests/wifi_stream_test.py` (new, port 8797), added to `tests/run_all.py` as `("streaming over wi-fi", "wifi_stream_test.py")`

**Interfaces:**
- **Produces, Python:**
  - `phone_ticket_new(device_id: str, path: str) -> str`
  - `phone_ticket_path(ticket: str) -> str | None` (refreshes last use)
  - `phone_tickets_drop(device_id: str | None = None) -> None` (None drops all)
  - `phone_subs_for(path: str) -> list[str]` (absolute paths)
  - `phone_resume_for_key(key: str) -> int` (seconds, 0 if none)
- **Produces, routes:**
  - POST `/phone/play` {key}, Bearer, returns
    `{"url": "/phone/stream/<t>", "subs": ["/phone/stream/<t>/sub/0", …], "title": str, "resume": int}`
  - GET `/phone/stream/<t>` and `/phone/stream/<t>/sub/<n>`, no Bearer
  - `/phone/hello` gains `"device_id": sync_device_id()`

- [ ] **Step 1: Write the failing tests** in `tests/wifi_stream_test.py`.
  - **Setup.** Copy the `isolate` and `call()` setup from
    `phone_link_test.py`. Make a temp video `Don’t Look Up – 2021.mkv`
    (300 000 bytes) with `Don’t Look Up – 2021.en.srt` and `…forced.ass`
    beside it, and point a movie row's path at it.
  - **The checks:**
    - `play needs a token`: POST `/phone/play` without Bearer gives 401.
    - `play gives a ticket`: 200, `url` matches `^/phone/stream/[A-Za-z0-9_-]{32}$`, `len(subs) == 2`, `resume == 0`.
    - `resume comes from the PC`: set `resume_pos=1234` and expect `1234`.
    - `unknown key 404`, and `episode not on the PC 404` (Review Focus 4).
    - `sleeping drive 503`: monkeypatch `n.media_file_check` to return None.
    - `stream whole`: GET url gives 200, the body equals the file, `Content-Disposition` starts `inline`, and `Content-Type` is `video/x-matroska`.
    - `stream range at the end`: `Range: bytes=299999-` gives 206 with 1 byte; `bytes=300000-` gives 416 (Review Focus 2).
    - `sub 0 served, sub 9 404`.
    - `bad ticket 404`.
    - `a ticket names one file`: ticket A with `?key=` of file B, or `/phone/stream/<A>/../…`, never returns B's bytes.
    - `forget drops tickets`: after `n.phone_forget(PHONE)` the old url gives 404.
    - `link off drops tickets`.
    - `expires`: set the ticket's last use to `time.time()-43201`, then 404.
    - `twenty per device`: mint 21; the first is gone and the 21st works.
    - `hello says device_id`.
- [ ] **Step 2: Run them** with `python tests/wifi_stream_test.py`.
  Expected: FAILs (no such route).
- [ ] **Step 3: Implement.**
  - **Refactor.** `send_media(key)` resolves the path and calls a new
    `send_path(path, inline=False)` holding today's body. Inline mode
    sends `Content-Type` from `mimetypes.guess_type` (falling back to
    `application/octet-stream`; register `.mkv` as `video/x-matroska`) and
    `inline; filename=…` with the same RFC 5987 encoding.
  - **Tickets** live in `_PHONE_TICKETS = {}` as `ticket -> [device_id, path, last_used]`, guarded by `_PHONE_LOCK`.
  - **`/phone/play`** goes in `do_POST` after `gate()`. It uses
    `phone_path_for_key` and `media_file_check` with the same 404/503
    wording as `send_media`. The `title` is the basename without its
    extension.
  - **`/phone/stream/`** is handled in `do_GET` before `gate()`. It still
    calls `from_home()`, and `sub/<n>` indexes `phone_subs_for(path)`.
  - **Subtitles.** `phone_subs_for` lists `.srt` and `.ass` files in the
    video's folder whose name starts with the video's base name, sorted.
  - **Dropping tickets.** `phone_forget` and `phone_link_stop` call
    `phone_tickets_drop`.
- [ ] **Step 4: Run** `python tests/wifi_stream_test.py` and
  `python tests/phone_link_test.py`. Expected: all PASS.
- [ ] **Step 5: Commit** "Wi-Fi streaming: play tickets on the PC's phone link".

### Task 2: Pairing over the cable

**Files:**
- Modify: `nextup.py`:
  - add `phone_pair_direct` beside `phone_pair_finish` (~11909)
  - `usb_send_library` (~12845)
  - the Android-only `/api/` routes, next to `/api/share/import`
- Test: `tests/usb_phone_test.py` (extend), `tests/wifi_stream_test.py`

**Interfaces:**
- **Consumes:** `phone_link_set`, `phone_addresses`, `_usb_phone_call`.
- **Produces:**
  - `phone_pair_direct(device_id: str, name: str) -> str`: the token,
    or AppError for a bad or taken id. It shares one storing helper with
    `phone_pair_finish`, `_phone_store_device(device_id, name) -> token`.
  - Phone route POST `/api/link/pair`
    `{token, pc, port, addresses: [str], pc_id}` → `{"ok": true}`. It
    stores `CONFIG["pc_link"] = {token, pc, port, addresses, pc_id, last_ip: None}`.
  - The `usb_send_library` result gains `"streaming": "on" | "<reason it isn't>"`.

- [ ] **Step 1: Failing tests.**
  - In `wifi_stream_test.py`:
    - `direct pairing gives a working token`: `/phone/hello` with it gives 200.
    - `direct pairing refuses a bad id`, and `…this PC's own id`.
    - `re-pairing replaces the old token`: the old one gives 401.
  - In `usb_phone_test.py`, wherever it fakes the phone for a send:
    - `the send pairs the phone`: the fake phone received `/api/link/pair` with a token that `phone_device_for_token` accepts.
    - `result says streaming on`.
    - `a port that won't open is reported, the send still succeeds`: monkeypatch `phone_link_start` to raise OSError.
- [ ] **Step 2: Run both suites.** Expected: the new checks FAIL.
- [ ] **Step 3: Implement.**
  - **The send step** goes after `usb_swap_history`, using the device id
    that call returned. That needs `usb_swap_history` to also return
    `device_id`. It's skipped with `streaming: "update the phone app"`
    when the phone has no `/api/link/pair` (404).
  - **The `/api/link/pair` route** exists only when
    `PLATFORM == "android"` and writes with `save_json(CONFIG_PATH, CONFIG)`.
- [ ] **Step 4: Run** `wifi_stream_test.py`, `usb_phone_test.py` and
  `phone_link_test.py`. Expected: PASS.
- [ ] **Step 5: Commit** "Wi-Fi streaming: SEND MY LIBRARY pairs the phone".

### Task 3: The phone finds the PC

**Files:**
- Modify: `nextup.py`:
  - a new "the PC, from the phone" section after the phone link section
  - `/api/status`
  - a new route POST `/api/link/check`
- Test: `tests/wifi_stream_test.py`

**Interfaces:**
- **Produces:**
  - `PC_LINK = {"up": False, "base": None, "pc": None, "needs_pairing": False, "checked": 0.0}`
  - `pc_link_check(force: bool = False) -> dict`. It returns `PC_LINK`.
    Unless forced, it reuses a check younger than 60 s.
  - `pc_link_call(method: str, path: str, body=None, timeout=10) -> (status: int, data: dict | bytes)`.
    It sends Bearer, uses `PC_LINK["base"]`, and on a connection error
    sets `PC_LINK["up"] = False`.
  - `/api/status` gains `"pc_link": {"up", "pc", "needs_pairing"}` on Android.
  - POST `/api/link/check` → runs `pc_link_check(force=True)` in a thread
    and returns the current `PC_LINK` straight away.
- **The order addresses are tried in:** `last_ip`, then `addresses`
  (de-duplicated), then UDP. UDP sends `NEXTUP?` to
  `("255.255.255.255", port)` with `SO_BROADCAST`, and the first reply
  whose JSON has `"nextup": 1` gives the IP. The address that answered
  becomes `last_ip` and is saved. A 401 sets `needs_pairing=True, up=False`.

- [ ] **Step 1: Failing tests.** They run with `n.PLATFORM = "android"`
  and a real `phone_link_start(8797, "127.0.0.1", udp_port=8797)`, paired
  by `phone_pair_direct`.
  - `finds the PC at a stored address`: `addresses=["127.0.0.1"]` gives `up` True and `pc` set.
  - `a dead first address is skipped` (Review Focus 3): `addresses=["10.255.255.1","127.0.0.1"]` gives up True and `last_ip == "127.0.0.1"`.
  - `finds it by calling out`: no addresses, and the UDP broadcast swapped
    for a call to `127.0.0.1` through an overridable `PC_LINK_CALL_TO`
    defaulting to `"255.255.255.255"`.
  - `forgotten reads as needs pairing`.
  - `PC off reads as down within 4 s`: the link stopped, then a timed call.
  - `status carries pc_link`.
  - `a recent check is reused`: the second call within 60 s makes no request.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement** as specified above.
- [ ] **Step 4: Run** `wifi_stream_test.py`. Expected: PASS.
- [ ] **Step 5: Commit** "Wi-Fi streaming: the phone finds the PC".

### Task 4: History both ways over Wi-Fi

**Files:**
- Modify: `nextup.py` (the same phone-side section)
- Test: `tests/wifi_stream_test.py`

**Interfaces:**
- **Consumes:** `pc_link_call`, `share_export()`, `share_import(text, sender)`.
- **Produces:**
  - `pc_link_sync() -> dict | None`. It returns
    `{"to_pc": kept, "from_pc": arrived}`, or None when the link is down.
    It never raises: failures go to `log_problem("wi-fi sync")`.
  - `pc_link_sync_soon()` starts `pc_link_sync` in a daemon thread, at
    most one at a time.
  - Calls to `pc_link_sync_soon()`:
    - after `android_play_finished`
    - after a `pc_link_check` that came up, if the last sync was more than
      600 s ago (`PC_LINK["synced"]`)
- **Sender:** the PC's lines go into `share_import` under
  `sender = CONFIG["pc_link"]["pc_id"]`, falling back to the hello's
  `device_id`. That's the same file name the cable swap uses.

- [ ] **Step 1: Failing tests.** Run the PC and the "phone" as two
  isolated homes in one process: the PC's DB through `n.db` while the link
  serves, and the phone's through swapping `n.DB_PATH`, the way
  `tests/usb_phone_test.py` does. If one process is impractical, run the
  PC as a subprocess with `tests/devserve.py`.
  - `phone stop event reaches the PC`: log a `stopped` on the phone with
    position 600 and run the sync; the PC's history has the uid.
  - `PC rating reaches the phone`.
  - `a second sync adds nothing`: both counts are 0, or no new rows.
  - `link down gives None, no raise`.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `wifi_stream_test.py` and `usb_phone_test.py`.
  Expected: PASS.
- [ ] **Step 5: Commit** "Wi-Fi streaming: history both ways after each sitting".

### Task 5: Playing a streamed item (phone server side)

**Files:**
- Modify: `nextup.py`:
  - `log_event` (~2158)
  - `/api/play` (~13413)
  - `note_now_playing` on Android (~4253)
  - `android_play_finished` (~22611)
  - `android_play` (~22688)
  - the elsewhere rows (~10150–10200, and the `show_elsewhere` listing ~5349)
  - new route GET `/api/elsewhere/episodes`
- Modify: `android/src/mobile/app.py`: `open_in_player`, and the `ANDROID_PLAYER` lambda
- Test: `tests/wifi_stream_test.py`, `tests/android_core_test.py`

**Interfaces:**
- **Consumes:** `pc_link_check`, `pc_link_call`, `phone_file_key`, `pc_link_sync_soon`.
- **Produces:**
  - `log_event(..., ident=None)`: an explicit
    `(tmdb_id, season, episode, show_title)` used when `item_id` is None.
  - `elsewhere_progress(kind: str, tmdb_id: str, season=None, episode=None) -> {"position": int, "watched": bool}`.
    It comes from history rows for that identity, all origins, latest
    `stopped` or `watched`.
  - **Elsewhere rows gain `"stream": True`** while `PC_LINK["up"]`:
    - films always
    - shows when the snapshot lists any episode
  - **`/api/elsewhere/episodes?tmdb_id=`** returns
    `{"title", "seasons": [{"season": n, "episodes": [{"episode", "title", "watched", "position"}]}], "next": {"season","episode"} | None}`.
    `next` is the first episode after the last watched one, else S1E1.
  - **`/api/play` with `{"stream": {"kind": "movie"|"episode", "tmdb_id", "season"?, "episode"?}, "resume"?: bool}`:**
    1. `pc_link_check()`
    2. POST `/phone/play`, with the 503 retry from Global Constraints
    3. `start = max(elsewhere_progress.position, pc resume)` (0 if the
       last was watched), and 0 if the page asked to start over
    4. `android_play(base+url, start, subs=[base+s…])`
    5. `log_event(kind, None, title, "played", ident=…)`
    6. Sitting: `_ANDROID_SITTING.update(kind, id=None, stream=ident, title, started_at)`
    - While retrying it returns `{"ok": True}`; on failure, AppError with the copy from Global Constraints.
  - **`android_play(path, start=0, subs=None)`** and
    `ANDROID_PLAYER(path, start, subs)`. app.py's lambda passes `subs` on.
  - **`android_play_finished`, for a sitting with `stream`:** logs
    `watched` or `stopped` with `ident` and position/total (the same
    `MIN_WATCH_SECONDS` rule). It doesn't touch local rows. Then
    `pc_link_sync_soon()`, for every sitting.
  - **`open_in_player(app, nextup, path, start, subs=None)`.** A path
    starting `http` uses `Uri.parse(path)`, with no grant flag and no
    MediaStore lookup. `subs` becomes the `"subs"` extra as a `Uri[]`
    (`jarray(Uri)`) plus `"subs.enable"` with the first.
- **Waking state:** the page polls nothing. `/api/play` blocks for up to
  10 s during the retry, and the page shows the waking copy while its
  request is pending for more than 1.5 s.

- [ ] **Step 1: Failing tests** (Android mode, a paired loopback link, and
  a fake `ANDROID_PLAYER` that records its arguments):
  - `elsewhere film marked stream while up, not when down`.
  - `elsewhere episode the PC lacks isn't offered` (Review Focus 4): it's
    missing from `/api/elsewhere/episodes`, and a stream play of it raises.
  - `stream play hands mpv an http URL and subs`.
  - `start is the later of phone and PC`: phone history 300 and PC 1234
    give 1234; phone 2000 and PC 1234 give 2000.
  - `finish logs a stop on the tmdb identity`.
  - `the next play starts there`.
  - `copied later keeps the point` (Review Focus 5): after streaming to
    600, a local movie row with the same tmdb gets
    `resume_position(...) == 600` once `repair` or `sync_apply` runs.
    Otherwise assert `elsewhere_progress` gives 600, and note it in the dev
    notes.
  - `next episode after the last watched`.
  - `503 retried then reported`: patch the sleep to no-op and make
    `media_file_check` None, expecting the exact copy.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement** as above.
- [ ] **Step 4: Run** `wifi_stream_test.py`, `android_core_test.py` and
  `audio_delay_test.py`. Expected: PASS.
- [ ] **Step 5: Commit** "Wi-Fi streaming: the phone plays from the PC".

### Task 6: The page

**Files:**
- Modify: `nextup.py` PAGE:
  - tile builder (~18036–18215)
  - the peek
  - `nextupBack`
  - the CSS near `.tile.elsewhere` (~15062)
  - startup and visibility
- Test: `tests/android_core_test.py` (source checks); real check in `tests/phone_serve.py`

**Interfaces:**
- **Consumes:** `item.stream`, `/api/play {stream}`, `/api/elsewhere/episodes`, `/api/link/check`, `STATUS.pc_link`.
- **Produces, in the JS:**
  - **Tiles:** an elsewhere item with `stream` gets the class `streamable`
    and no grey (CSS: `.tile.elsewhere.streamable .art{filter:none}` and so
    on), plus a `.wifimark` badge (an inline SVG Wi-Fi glyph) in place of
    the elsewhere badge.
  - **Peek:** PLAY shows for streamable items. For a film it posts
    `{stream:{kind:'movie', tmdb_id}}`. For a show it posts the episode
    `next` from `/api/elsewhere/episodes`, and the label reads
    "PLAY S2E4".
  - **DETAILS** on a streamable show opens `#elsewhere-eps`, a sheet using
    the details sheet's CSS: seasons, then episode rows, each with a play
    button and a watched tick. It closes with Back (`nextupBack`) and the
    sheet swipe.
  - **Waking:** a pending play over 1.5 s shows "Waking the PC's drive…" in
    the peek's play button.
  - **Checks:** `post('/api/link/check')` runs on load and on
    `document.visibilitychange` to visible, on Android only. 4 s later
    the library re-renders if `pc_link.up` changed (a single `setTimeout`,
    not an interval).

- [ ] **Step 1: Failing source checks** in `android_core_test.py`:
  - `streamable tiles aren't grey` (the CSS rule is present)
  - `link check on visibility` (the `visibilitychange` handler posts `/api/link/check`)
  - `no interval polls the link` (no `setInterval` near `link/check`)
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run `android_core_test.py`, then a visual check.**
  - Start the "nextup-phone" preview against a sandbox paired to a
    loopback link that `tests/phone_serve.py` starts beside it. Add a
    `--with-pc` flag that runs `phone_link_start` on 8797 from a second
    isolated home.
  - Check in portrait and landscape: a streamable tile, the peek with
    PLAY, the show episode sheet, and Back closing it.
  - Screenshot each.
- [ ] **Step 5: Commit** "Wi-Fi streaming: greyed tiles light up when the PC is there".

### Task 7: Version, notes, the real phone

**Files:**
- Modify: `nextup.py` (`APP_VERSION = "0.1.75"`), `android/pyproject.toml`
  (version), `DEVELOPMENT_NOTES.md` (a v0.1.75 entry), `PLANNED.md`
  (mark it done), `tests/run_all.py` (already added in Task 1; check)

- [ ] **Step 1: Run** `python tests/run_all.py`. Expected: every suite
  passes, and the guarded files are unchanged.
- [ ] **Step 2: Write the dev notes entry.**
  - What exists and why tickets.
  - The NordVPN "Invisibility on LAN" note.
  - The first-use Windows Firewall prompt.
  - Any deviation from the spec.
- [ ] **Step 3: Bump the version and commit**
  "v0.1.75: stream from the PC over home Wi-Fi".
- [ ] **Step 4: On the real devices.**
  - Restart the PC app.
  - Ask the user to plug in the S24, then run `android/build.py`.
  - Run SEND MY LIBRARY, and confirm `streaming: on` and that the Firewall
    prompt was answered.
  - Unplug. Stream a film that isn't on the phone, seek, and stop halfway.
  - Confirm the PC's history has the stop and its resume point.
  - Stop the PC app, then resume the phone app: the tile is grey again.
- [ ] **Step 5: Report** the outcome to the user, with the device checks and anything that failed.
