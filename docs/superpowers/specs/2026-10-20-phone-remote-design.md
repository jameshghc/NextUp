# The phone as a remote for the PC — design

2026-10-20. Builds on the sketch in PLANNED.md (2026-10-19). Decided with
the user: a Remote tab, and Play on PC in the first version.

## What it's for

From the phone, on the home Wi-Fi:
- control whatever is playing on the PC (the TV), as the PC's own remote
  window does;
- start something on the PC from the phone's library.

Success:
- With the PC app running and the phone paired (SEND MY LIBRARY), a Remote
  tab appears. It shows what's on with a seek bar, and every control acts
  within about a second.
- "Play on PC" on a tile starts it on the PC and opens the Remote.
- "Are you still watching?" can be answered from the phone.
- No polling in the background. The v0.1.74 battery numbers hold.

## What exists

- **The PC remote.**
  - `remote_state()`: alive, playing, volume, muted, paused, track info,
    audio delay, `is_episode`, `queue_count`, channels and presets.
  - The desktop routes `/api/remote/{volume,toggle,channel,delay,episode,
    skip,subtitles,stop}`, each a few lines in `Handler.do_POST`.
- **The Wi-Fi link (v0.1.75).**
  - `PhoneHandler` on 8790: Bearer token, home network only, the phone's
    routes and nothing else.
  - On the phone: `pc_link_check`, `pc_link_call`, `PC_LINK`.

## Design

### 1. One set of remote actions (PC)

`remote_do(action, data) -> dict`:
- **Actions** (moved out of the route bodies unchanged): `volume`,
  `toggle`, `channel`, `delay`, `episode`, `skip`, `subtitles`, `stop`.
- **New actions:**
  - `seek` `{to: seconds}` or `{by: ±seconds}`: mpv `seek … absolute` or
    `relative`.
  - `afk` `{still: bool}`: `afk_answer`.
- **Returns** `remote_state()`, or `dict(remote_state(), subtitles=…)` for
  `subtitles`. Raises `AppError` exactly where the routes did.
- **Desktop routes** become `return self.send_json(remote_do(name, data))`,
  so the two remotes can't drift apart.

`remote_state()` gains:
- `position` and `duration` (seconds, from the monitor's `NOW_PLAYING`,
  else mpv);
- `title`, `sub` and `art` of what's playing;
- `afk` (`afk_state()`, or None).

### 2. The remote over the Wi-Fi (PC, `PhoneHandler`)

- **GET `/phone/remote/state`** → `remote_state()`, with art as a
  `/phone/art/…` path.
- **POST `/phone/remote/<action>`** for the actions above.
  - Unknown action: 404.
  - `AppError`: `{error}` with 200, the app's convention.
  - Every POST calls `seen_you()`, so using the phone counts as being there
    for the sleep timer.
- **POST `/phone/remote/play`** `{kind, tmdb, season?, episode?, resume}`:
  - `movie`: that film's file here.
  - `episode`: that episode.
  - `tvshow`: this PC's next-up episode of the show, the same choice the
    PC's own tile PLAY makes (`next_up`, else the first episode).
  - It plays through the same path as the desktop `/api/play` (mpv, resume
    point, `log_event` "played", `note_now_playing`). Resume defaults on.
  - Returns `remote_state()`, or a 404 / `{error}` for something this PC
    hasn't got.
- Nothing else from the desktop server is reachable. A test names every
  route that answers.

### 3. The phone's side (server)

- `/api/pcremote/state` (GET) and `/api/pcremote/<action>` (POST) pass
  straight through via `pc_link_call`, so the token never reaches the page.
  When the PC isn't there: `{error: "The PC isn't on the Wi-Fi right
  now."}`.
- Library rows gain `on_pc: true` while the link is up and the PC's
  catalogue has the title:
  - films by tmdb in `snapshot_movies`;
  - shows by tmdb in `snapshot_shows`;
  - elsewhere rows that are already `stream`.

### 4. The phone's page

- **A Remote tab** after Channels, shown only while `pc_link.up`. If the
  PC goes away while it's open, the page says so and offers Library.
- **The Remote screen, top to bottom:**
  - What's on: art, title, the line under it ("S02E04 · …", the year), and
    "Nothing playing on the PC" when idle.
  - A seek bar with elapsed and remaining. Dragging seeks on release.
  - Big ⏪10 · ⏯ · 30⏩.
  - Volume − / + with the level, and mute.
  - Audio delay −100 / +100 with the value, remembered per film (the PC
    does that already).
  - Subtitles and audio track buttons, showing the current language; they
    cycle. Subtitles has "Find subtitles" as on the PC.
  - Previous / next episode (episodes only) and skip (channel or queue
    only).
  - The six channel presets as chips, and stop.
  - If "are you still watching?" is up on the PC: a card at the top with
    STILL HERE / THAT'S ENOUGH and the countdown.
- **Refresh.** `/api/pcremote/state` once a second, only while the Remote
  tab is showing and the page is visible. It stops on leaving the tab or
  the app going to the background. Every action returns the new state, so
  presses show at once.
- **A "Now playing on PC" strip** at the bottom of the other screens while
  the PC is playing: art, title, ⏯. Tapping it opens the Remote.
  - It refreshes on app open/resume (with `lookForPC`) and every 10 s
    while the app is visible and the link is up. It stops when hidden.
- **Play on PC.**
  - In a tile's peek, beside PLAY: "▶ ON PC" when `on_pc`. A show plays
    the PC's next-up episode.
  - In the elsewhere-show episode sheet, a small "ON PC" per episode.
  - Afterwards, the Remote opens.

### 5. Errors

| Situation | What happens |
|---|---|
| PC app off | The Remote tab hides at the next check. A press shows "The PC isn't on the Wi-Fi right now." |
| Nothing playing | Controls greyed, "Nothing playing on the PC"; Play on PC still works. |
| Forgotten phone (401) | The tab hides, same as streaming (needs a cable send). |
| PC lacks the file | Play on PC: "The PC doesn't have that any more." |

## Out of scope

- The phone's volume keys driving the PC.
- The queue on the phone.
- Channel guide browsing beyond the presets.

## Testing

- **`tests/phone_remote_test.py`**, against a loopback link with mpv faked
  (`mpv_get`/`mpv_command`/`mpv_alive` patched) and paired by
  `phone_pair_direct`:
  - every action through `/phone/remote/<action>` matches calling it on
    the desktop route;
  - seek absolute and relative;
  - the afk answer;
  - unknown action 404, and no token 401;
  - `/phone/remote/play` for a film, an episode, and a show (next-up);
  - an unknown tmdb gives an error;
  - every POST counts as being there (`afk_idle` resets);
  - the state has position, duration, title and afk.
- **The phone side:** the passthrough with the PC down gives the copy
  above, and `on_pc` is marked only while the link is up.
- **Page source checks:**
  - the tab is hidden unless the link is up;
  - polling is tied to the tab and visibility, with no interval left
    running on hide;
  - the strip, and the ON PC button.
- **On the S21 and the real PC:**
  - send the library (pairing);
  - play a film on the PC from the phone;
  - pause, seek, volume, delay, subtitles;
  - answer the AFK question;
  - the strip appears on the other tabs.
