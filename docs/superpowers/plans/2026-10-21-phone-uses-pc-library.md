# The Phone Draws on the PC's Library — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** While the PC is reachable, the phone's Now, Continue and Channels
come from the PC. Each title offers ▶ HERE and/or ▶ ON PC.

**Architecture:**
- **PC:** three read-only `PhoneHandler` routes return `build_tonight`,
  `available_genres` and the channel schedule, with every item carrying an
  `ident` (tmdb identity).
- **Phone:** passes them through `pc_link_call`, and plays HERE through
  `/api/play {stream}` (a local file when it has one), or ON PC through
  `/phone/remote/play` / `channel`.

**Tech Stack:** stdlib Python and the page JS in `nextup.py`.

**Spec:** `docs/superpowers/specs/2026-10-21-phone-uses-pc-library-design.md`

## Global Constraints

- All code in `nextup.py`, LF; patches via scratchpad scripts.
- Phone routes on `PhoneHandler` only (Bearer, home network).
- AppError comes back as `{error}` with 200.
- No new polling. Pages fetch on open or refresh only.
- Copy:
  - "▶ HERE"
  - "▶ ON PC"
  - "From the PC's library"
  - "The PC isn't on the Wi-Fi right now."
- Tests in `check()` style; new suites go in `tests/run_all.py`.

## Review Focus

1. **A pick with no tmdb id** (an unidentified film): ON PC only, never a
   broken HERE. Test in Task 1.
2. **A channel's current file is the second episode of a two-episode
   block:** the `ident` and offset point at that episode and the offset
   within it. Test in Task 1.
3. **The phone has the title locally:** HERE plays the local file, not a
   stream. Test in Task 2.
4. **The PC goes away while Now is open:** the next fetch falls back to
   `/api/tonight` without an error banner. Source and behaviour checks in
   Task 3.
5. **A channel sitting on the phone is stopped by hand:** no auto-continue.
   Test in Task 2.

---

### Task 1: PC routes (`/phone/now`, `/phone/genres`, `/phone/channels`)

**Files:**
- `nextup.py`: `PhoneHandler.do_GET`, plus helpers next to
  `phone_remote_state`.
- Test: `tests/phone_pclib_test.py` (new, port 8789), added to `run_all`.

**Produces:**
- `ident_for(kind, item_id) -> dict|None`, from `sync_identity`:
  `{kind, tmdb, season?, episode?}`.
- `phone_art(url) -> str`: `/art/x` → `/phone/art/x`.
- `/phone/now` (the same query parameters as `/api/tonight`) →
  `{picks:[…+ident], continue:[…+ident], reset}`. It does not call
  `remember_offer`.
- `/phone/genres?kind&with` → `{genres}`.
- `/phone/channels` → `{channels:[{id,name,live,youtube?, now:{…channel_summary, ident?, offset}}]}`.
  `offset` and `ident` come from
  `channel_play_target(block, now["offset"])`, and there's no `ident` for
  YouTube or live channels.

**Steps:**
1. Write the failing tests:
   - the routes need a token;
   - picks have `ident`, art under `/phone/art/`, and honour `kind=film`;
   - continue items have `ident`;
   - a pick without a tmdb id has no `ident` (Review Focus 1);
   - genres equal `available_genres`;
   - channels: offset ≥ 0, and an episode block resolves to the right
     episode and offset (Review Focus 2);
   - live channels have no `ident`.
2. Run them: they fail.
3. Implement.
4. Run them: they pass.
5. Commit.

### Task 2: Phone side — passthrough, play here, channel sittings

**Files:**
- `nextup.py`: the phone-side section next to `pc_remote_call`, `/api/play`
  (stream branch), `pc_stream_play`, `_stream_finished`.

**Produces:**
- GET `/api/pcnow`, `/api/pcgenres` and `/api/pcchannels`, passed through.
  Art goes via `/api/pcremote/art/`, and the PC being away gives
  `{error: PC_AWAY}`.
- `pc_stream_play(stream, resume=False, start=None, channel=None)`:
  - when a local movie or episode row has the same tmdb identity, it plays
    that through `play_local` instead (Review Focus 3);
  - an explicit `start` overrides resume;
  - `channel` is stored on the sitting.
- `/api/play {stream, start?, channel?}` passes them on.
- In `_stream_finished` / the local finish: when the sitting had a
  `channel` and was completed, the phone fetches `/phone/channels` and plays
  that channel's `now` (HERE) at its offset. A stopped sitting doesn't
  continue (Review Focus 5).

**Steps:**
1. Write the failing tests (Android mode, loopback PC, fake
   `ANDROID_PLAYER`):
   - the passthroughs, and their copy with the PC away;
   - HERE with a local match plays the local path;
   - an explicit start is used;
   - a completed channel sitting plays the next item;
   - a stopped one doesn't.
2. Run them: they fail.
3. Implement.
4. Run them: they pass.
5. Commit.

### Task 3: The page (phone)

**Files:**
- `nextup.py` PAGE: `tonightParams` / `loadTonight` fetch source, the
  chooser's `chooserAvail`, `pickCard` buttons, `altCard`, the Continue
  cards, `loadChannels`, and the CSS.

**Produces:**
- `nowSource()` → `'/api/pcnow'` when `body.android` and `pcLinkUp`, else
  `'/api/tonight'`. Genres likewise.
- If a PC fetch returns `{error}`, it falls back to the local route once
  (Review Focus 4).
- `playChoice(item) -> HTMLElement`:
  - ▶ HERE: `/api/play {stream: ident}`; for a local item, the usual
    local play;
  - ▶ ON PC: `playOnPC(ident)`;
  - each shown only when it applies.
  - It's used by the pick card (the main row), the alternatives and the
    Continue cards.
- A "From the PC's library" line under the chooser while the PC source is
  in use.
- Channels: while `pcLinkUp` it renders `/api/pcchannels`. Each card has
  ▶ HERE (when it has an `ident`: `/api/play {stream: ident, start: offset,
  channel: id}`) and ▶ ON PC (`remoteSend('channel', {channel: id})`, then
  the Remote).

**Steps:**
1. Write the failing source checks in `android_core_test`.
2. Run them: they fail.
3. Implement.
4. Run them: they pass. Then a visual check in `phone_serve --with-pc`
   (Now, Continue and Channels, portrait).
5. Commit.

### Task 4: Version, notes, the device, review

1. Run `run_all`: everything passes.
2. Bump the version to **0.2.1**, write the DEVELOPMENT_NOTES entry and
   update PLANNED. Commit.
3. Build for the S21 and check it on the device: the Now picks come from
   the PC, and HERE and ON PC both work on a film the phone doesn't have.
4. A final whole-branch review by a fresh agent, then one fix pass.
