# The Phone as a Remote for the PC — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** On the home Wi-Fi, the phone controls what's playing on the PC
and can start something there.

**Architecture:**
- **PC:** the desktop remote's route bodies become one function,
  `remote_do(action, data)`, which both the desktop routes and new
  `PhoneHandler` routes call. `/phone/remote/play` starts a film or episode
  through the same code as `/api/play`.
- **Phone:** `/api/pcremote/*` passes calls through `pc_link_call`, and the
  page gets a Remote tab, a now-playing strip, and ON PC buttons.

**Tech Stack:** Python stdlib and the embedded page JS in `nextup.py`.
`android/` is only rebuilt.

**Spec:** `docs/superpowers/specs/2026-10-20-phone-remote-design.md`

## Global Constraints

- **Line endings and patches.** All code goes in `nextup.py`, LF only.
  Write patches with Python scripts in the scratchpad.
- **Version.** It becomes **0.2.0** at the end (the user's request), in
  `nextup.py` and `android/pyproject.toml`.
- **What the phone can reach.** Phone routes are on `PhoneHandler` only:
  Bearer token, home network. Nothing else from the desktop server becomes
  reachable.
- **Errors.** `AppError` comes back as `{error}` with HTTP 200 (the app's
  convention).
- **Polling.**
  - The Remote: once a second, only while the Remote tab is showing and
    `document.visibilityState === 'visible'`.
  - The strip: every 10 s while visible and the link is up.
  - Both stop on hide. Nothing runs in the background.
- **Copy:**
  - "The PC isn't on the Wi-Fi right now."
  - "Nothing playing on the PC"
  - "The PC doesn't have that any more."
  - "▶ ON PC"
  - "STILL HERE" / "THAT'S ENOUGH"
- **Tests.** `check()` style, sandboxed with `devserve.isolate`, and added
  to `tests/run_all.py`.

## Review Focus

1. **Seeking past the end or before 0** (dragging the bar to the edge):
   clamped to 0…duration-1, never an mpv error. Test in Task 1.
2. **Pressing a control with nothing playing:** `{error: "Nothing is
   playing."}` and the screen stays usable, never a 500. Test in Task 1.
3. **Play on PC for a show with no next-up** (all watched): plays the first
   episode rather than erroring. Test in Task 2.
4. **The PC going away while the Remote is open:** the next poll gets
   `{error}`, and the tab shows the copy without throwing. Source and
   behaviour checks in Tasks 3 and 4.
5. **Two quick presses** (+ + volume): each answers with the state after
   it; no race leaves the shown volume stale. That follows from every
   action returning `remote_state()`. Test in Task 1.

---

### Task 1: `remote_do` and the richer state (PC)

**Files:**
- Modify: `nextup.py`: `remote_state()` (~12060), and the
  `/api/remote/*` routes (~14600–14700) become one-liners.
- Test: create `tests/phone_remote_test.py`, port 8792, and add it to
  `tests/run_all.py`.

**Interfaces:**
- Produces:
  - `REMOTE_ACTIONS = ("volume","toggle","channel","delay","episode","skip","subtitles","stop","seek","afk")`
  - `remote_do(action: str, data: dict) -> dict`. It raises `AppError` as
    the routes did, and `AppError("No such control.")` for an unknown
    action.
- `remote_state()` gains `position`, `duration` (seconds or None),
  `title`, `sub`, `art` and `afk`.
- **`seek`:** `{to}` gives `mpv seek <clamped> absolute`; `{by}` gives
  relative, clamped so the result lands in 0…duration-1.

- [ ] **Step 1: Failing tests.** Fake mpv with a dict
  (`mpv_get`/`mpv_command`/`mpv_alive` patched, as in `afk_test`):
  - `volume +5 twice → 55 then 60`
  - `toggle pause`
  - `delay -100 → -100`
  - `seek to 30`
  - `seek by -9999 clamps to 0`
  - `seek to 999999 clamps to duration-1`
  - `afk still answers a pending question`
  - `nothing playing → AppError "Nothing is playing."`
  - `unknown action → AppError`
  - `state has position, duration, title, afk`
  - the desktop `/api/remote/volume` route gives the same as `remote_do`
- [ ] **Step 2: Run** `python tests/phone_remote_test.py`. Expected: FAIL
  (no `remote_do`).
- [ ] **Step 3: Implement.** Move each route body into `remote_do`
  unchanged, and point the routes at it.
- [ ] **Step 4: Run** `phone_remote_test.py`, `afk_test.py` and
  `queue_test.py`. Expected: PASS.
- [ ] **Step 5: Commit** "Remote: one set of actions, seek and afk added,
  state with position".

### Task 2: The remote over the Wi-Fi (PC, `PhoneHandler`)

**Files:**
- Modify: `nextup.py`: `PhoneHandler.do_GET`/`do_POST`, and a new
  `play_on_pc` next to `/api/play`. The `/api/play` local branch moves into
  `play_local(kind, item_id, resume) -> None` so both use it.
- Test: `tests/phone_remote_test.py`

**Interfaces:**
- Consumes: `remote_do`, `remote_state`.
- Produces:
  - GET `/phone/remote/state`
  - POST `/phone/remote/<action>` for `REMOTE_ACTIONS`
  - POST `/phone/remote/play` `{kind: "movie"|"episode"|"tvshow", tmdb,
    season?, episode?, resume?=true}` → `remote_state()`
  - `play_on_pc(kind, tmdb, season=None, episode=None, resume=True) ->
    None`. `tvshow` uses `show_detail(id)["next_up"]`, else the first
    episode. It raises `AppError("The PC doesn't have that any more.")`.
- Every remote POST calls `seen_you()` first.
- The state's art is rewritten to `/phone/art/<name>`.

- [ ] **Step 1: Failing tests** on a loopback `phone_link_start(8792)`,
  paired by `phone_pair_direct`, with `mpv_play` patched to record:
  - `no token 401`
  - `state over the wire`
  - `volume over the wire matches remote_do`
  - `unknown action 404`
  - `play film`
  - `play episode`
  - `play show → its next-up`
  - `play show all watched → first episode` (Review Focus 3)
  - `unknown tmdb → the copy`
  - `a press counts as being there` (`afk_idle() < 2` after a POST)
  - `art is a /phone/art path`
  - `only the listed /phone/remote routes answer`
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `phone_remote_test.py`, `wifi_stream_test.py` and
  `phone_link_test.py`. Expected: PASS.
- [ ] **Step 5: Commit** "Remote: reachable from the paired phone, and
  play on PC".

### Task 3: The phone's passthrough and `on_pc`

**Files:**
- Modify: `nextup.py`: the phone-side section next to
  `pc_stream_play`, `Handler` routes, and `elsewhere_rows` plus the local
  browse rows.
- Test: `tests/phone_remote_test.py`

**Interfaces:**
- Consumes: `pc_link_call`, `pc_link_check`, `PC_LINK`.
- Produces:
  - GET `/api/pcremote/state` and POST `/api/pcremote/<action>`: Android
    only, passed through. When the PC is down:
    `{"error":"The PC isn't on the Wi-Fi right now."}`.
  - Rows gain `on_pc: true` (Android, link up, tmdb in
    `snapshot_movies`/`snapshot_shows`).
  - `pc_remote_call(method, path, body=None) -> dict`.

- [ ] **Step 1: Failing tests** (Android mode, the loopback PC from Task 2):
  - `passthrough state`
  - `passthrough action`
  - `PC down → the copy, no raise` (Review Focus 4)
  - `on_pc only while up`
  - `a local film the PC also has is on_pc`
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `phone_remote_test.py` and `android_core_test.py`.
  Expected: PASS.
- [ ] **Step 5: Commit** "Remote: the phone's passthrough, and on_pc on
  rows".

### Task 4: The page: Remote tab, strip, ON PC

**Files:**
- Modify: `nextup.py` PAGE:
  - the nav tabs and `switchTo`
  - a new `#view-remote`
  - the CSS
  - the tile peek and `openElsewhereShow`
  - `lookForPC`
- Test: `tests/android_core_test.py` (source checks), then a visual check
  with `tests/phone_serve.py --with-pc`.

**Interfaces:**
- Consumes: `/api/pcremote/*`, `item.on_pc`, `STATUS.pc_link`.
- Produces, in the JS:
  - `remoteRender(state)`, `remoteSend(action, data)`,
    `remotePoll(on: bool)`, `stripRender(state)`, `playOnPC(item)`.
  - The tab's `data-view="remote"` is hidden unless `pcLinkUp`.
  - `switchTo('remote')` starts the 1 s poll; leaving stops it. A
    `visibilitychange` to hidden stops both polls.

- [ ] **Step 1: Failing source checks:**
  - `remote tab hidden unless the link is up`
  - `polling tied to the tab and visibility` (`clearInterval` and
    `remotePoll(false)` on hide)
  - `strip on other tabs`
  - `ON PC in the peek`
  - `AFK card with STILL HERE / THAT'S ENOUGH`
  - `seek on release` (`change` event, not `input`)
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement.** The layout follows the spec's §4 list. It
  reuses `.kchip`, `.iconbtn`, `.play` and `apslider` styles, and the
  Glass rules apply automatically.
- [ ] **Step 4: Run `android_core_test.py`, then a visual check.**
  - In `phone_serve.py --with-pc`, make the pretend PC's mpv a fake that
    answers state.
  - Screenshot the Remote tab and the strip, and press each control,
    checking the fake mpv saw it.
- [ ] **Step 5: Commit** "Remote: the phone's Remote tab, now-playing strip
  and ON PC".

### Task 5: 0.2.0, notes, the real devices

- [ ] **Step 1: Run** `python tests/run_all.py`. Expected: every suite
  passes.
- [ ] **Step 2: Notes, version and commit.**
  - Write the DEVELOPMENT_NOTES entry, the PLANNED update, and the version
    **0.2.0** in both places.
  - Commit "v0.2.0: the phone as a remote for the PC".
- [ ] **Step 3: Build to the S21** (R5CR11XSBFX) with `android/build.py`,
  and `check_device.py`.
- [ ] **Step 4: Hand to the user.** Restart the PC app, then SEND MY
  LIBRARY with the S21 plugged in. Then I check through the adb tunnel:
  - `pc_link.up`
  - Play on PC
  - pause, seek and volume
  - the PC's `remote_state` changing
- [ ] **Step 5: Final whole-branch review** (a fresh reviewer), one fix
  pass, then report.
