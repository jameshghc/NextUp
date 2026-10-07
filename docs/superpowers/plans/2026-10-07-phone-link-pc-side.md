# Phone Link (PC side) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a paired phone reach the PC's Next Up over home Wi-Fi: fetch the library snapshot, download files, and exchange sync events. Nothing else is reachable.

**Architecture:** A second `ThreadingHTTPServer` on port 8790, off by default, served by a new `PhoneHandler` class. That class has *only* the `/phone/*` routes, so the allow-list holds by construction rather than by checking. Pairing is a 4-digit code (5 minutes, 5 tries) that is swapped for a random token; the PC keeps only the token's SHA-256. Sync reuses the existing jsonl event format and `sync_import`/`sync_apply`. Only the transport is new.

**Tech Stack:** Python stdlib only (`http.server`, `socket`, `hashlib`, `secrets`), inside `nextup.py`. Tests are plain scripts in the repo's `check()` style.

**Spec:** `docs/superpowers/specs/2026-10-07-android-app-design.md` (Component 1 and the sync transport in Component 4).

## Global Constraints

- Everything lives in `nextup.py`, in one new section headed `# --- the phone link ---`. Comments match the file's narrative voice.
- LAN port **8790**. Off by default (`CONFIG["phone_link"]["enabled"]` is False). The `127.0.0.1:8770` server is unchanged.
- Pairing code: 4 digits, valid **5 minutes**, dead after **5** wrong tries.
- Token: `secrets.token_urlsafe(32)`, sent as `Authorization: Bearer <token>`. The config stores only `hashlib.sha256(token).hexdigest()`.
- Requests are accepted only from loopback or private addresses (`ipaddress.ip_address(ip).is_private`). Anything else gets 403.
- No path ever comes from the phone. Files are chosen by key: `m<tmdb>` for a film, `e<show_tmdb>s<season>e<episode>` for an episode.
- Every test runs under `devserve.isolate`. The new suite joins `tests/run_all.py`.
- Version bump to **0.1.48**, a `DEVELOPMENT_NOTES.md` entry and a commit at the end, per the repo's habit.

## Review Focus

1. **Brute-forcing the code.** Five wrong guesses kill the code. A sixth guess, even the right one, fails. → Task 1 test `code dies after five wrong tries`.
2. **A bad `Range` header** (`bytes=999999999-`, `bytes=abc`, `bytes=5-2`). Expect 416 with `Content-Range: bytes */<size>` and no traceback. → Task 3 tests.
3. **A phone uploading lines that claim another device's id** (the PC's, or the Mac's). The PC keeps only lines whose `device_id` is that phone's paired id. → Task 4 test `foreign device lines dropped`.
4. **The file is missing, or E: is asleep.** `/phone/file` gives 404 with a JSON reason within the existing 3 s `media_file_check` bound, and never hangs the listener. → Task 3 test `missing file is 404`.
5. **A desktop route asked of the phone port, even with a valid token** (`/api/status`, `/api/sorter/aside`, `/`). Expect 404, because the handler doesn't have it. → Task 2 test.

---

### Task 1: Pairing and tokens

**Files:**
- Modify: `nextup.py`: new section `# --- the phone link ---`, placed just before `class Handler`
- Create: `tests/phone_link_test.py`

**Interfaces:**
- Produces:
  - `PHONE_PORT = 8790`
  - `phone_cfg() -> dict`: returns `CONFIG["phone_link"]`, creating `{"enabled": False, "devices": []}` if missing. Each device is `{"id": str, "name": str, "token_sha": str, "paired_at": str, "last_seen": str}`.
  - `phone_pair_start() -> dict`: makes a fresh code and returns `{"code": "0427", "expires": float}`. The code is held in the module dict `PHONE_PAIRING = {"code": None, "expires": 0, "tries": 0}`.
  - `phone_pair_finish(code: str, device_id: str, name: str) -> str`: returns the token, or raises `AppError` (expired, wrong, used up). `device_id` must match `^[0-9a-f]{16}$`. Re-pairing the same id replaces its entry. Success clears the code (one use).
  - `phone_device_for_token(token: str) -> dict | None`: compares in constant time with `hmac.compare_digest`, and updates `last_seen`.
  - `phone_forget(device_id: str) -> None`

- [ ] **Step 1: Write the failing tests** in `tests/phone_link_test.py`. Set up the `isolate` boilerplate as in `tests/empty_shows_test.py` (sandbox `nextup_phonelink`), then add these checks:
  - `code is four digits`: `re.fullmatch(r"\d{4}", phone_pair_start()["code"])`
  - `right code gives a token, stored only as a hash`: the token is ≥ 40 chars, the token does not appear in `json.dumps(CONFIG)`, and `phone_device_for_token(token)["id"] == "abcdef0123456789"`
  - `code is single use`: a second `phone_pair_finish` with the same code raises `AppError`
  - `expired code refused`: set `PHONE_PAIRING["expires"] = time.time() - 1`, and pairing raises
  - `code dies after five wrong tries`: five wrong codes, then the right one, still raises
  - `bad device id refused`: `"../x"` raises
  - `forget revokes`: after `phone_forget`, `phone_device_for_token(token) is None`
- [ ] **Step 2: Run** `python tests\phone_link_test.py`. Expect it to fail with `AttributeError: module 'nextup' has no attribute 'phone_pair_start'`.
- [ ] **Step 3: Implement** the Interfaces above. The code is `"%04d" % secrets.randbelow(10000)`. Save `CONFIG` with `save_json(CONFIG_PATH, CONFIG)` after each change.
- [ ] **Step 4: Run** the test. Expect `7/7 passed`.
- [ ] **Step 5: Commit:** `git add nextup.py tests/phone_link_test.py && git commit -m "Phone link: pairing code and tokens"`

### Task 2: The phone listener and its gate

**Files:**
- Modify: `nextup.py` (the phone link section)
- Modify: `tests/phone_link_test.py`

**Interfaces:**
- Consumes: `phone_device_for_token`, `phone_cfg` (Task 1)
- Produces:
  - `class PhoneHandler(BaseHTTPRequestHandler)` with `protocol_version = "HTTP/1.1"`, a silent `log_message`, and `send_json` (same shape as `Handler.send_json`). Its `do_GET`/`do_POST` run `self.gate()` first.
  - `PhoneHandler.gate() -> dict | None`: if the client IP isn't loopback or private, it sends 403 and returns None. If the bearer token is missing or unknown, it sends 401 `{"error": "not paired"}` and returns None. Otherwise it returns the device dict.
  - Routes in this task: `POST /phone/pair` (the **one** ungated route; body `{"code", "device_id", "name"}` → `{"token", "pc": snapshot_device_name()}`, or 403 with `{"error"}`), and `GET /phone/hello` → `{"ok": True, "pc": snapshot_device_name(), "version": APP_VERSION}`. Every other path gives 404.
  - `phone_link_start(port: int = PHONE_PORT, host: str = "0.0.0.0") -> None` and `phone_link_stop() -> None`. These start and stop the server on a daemon thread, and are idempotent. The server is held in `_PHONE_SERVER = [None]`.

- [ ] **Step 1: Write the failing tests.** Start with `phone_link_start(8799, "127.0.0.1")`. Write a small `call(method, path, token=None, body=None, headers=None)` helper with `urllib.request` that returns `(status, headers, bytes)` and also returns HTTP errors rather than raising them. Checks:
  - `pairing over the wire`: POST `/phone/pair` with a fresh code gives 200 with a token
  - `hello needs the token`: without a token, 401; with it, 200, and `version == APP_VERSION`
  - `desktop routes don't exist here, token or not`: `/`, `/api/status` and `/api/library/status` by GET, and `/api/sorter/aside` and `/api/play` by POST, all give 404 with a valid token
  - `wrong code over the wire is 403`
  - `stop closes the port`: after `phone_link_stop()`, connecting to 8799 raises `ConnectionRefusedError` (wrapped in `URLError`)
- [ ] **Step 2: Run.** Expect FAIL: `phone_link_start` is not defined.
- [ ] **Step 3: Implement** the Interfaces. The private check is `ipaddress.ip_address(self.client_address[0])` with `.is_private or .is_loopback`. Unknown routes give `self.send_json({"error": "no such thing"}, 404)`.
- [ ] **Step 4: Run.** Expect all checks so far to pass.
- [ ] **Step 5: Commit:** `"Phone link: listener, gate, pairing route"`

### Task 3: Snapshot and file downloads

**Files:**
- Modify: `nextup.py` (the phone link section, plus `PhoneHandler` routes)
- Modify: `tests/phone_link_test.py`

**Interfaces:**
- Consumes: `PhoneHandler.gate` (Task 2), `build_library_snapshot()`, `media_file_check(path)`, and `art_filename`/`ART_DIR` (all existing)
- Produces:
  - `phone_file_key(kind: str, tmdb: str, season: int = None, episode: int = None) -> str`, giving `"m603"` or `"e1396s1e2"`
  - `phone_snapshot() -> dict`: `build_library_snapshot()` with an added `"key"` and `"ext"` (lower-case, from the path, with no stat on the disk) on every movie and episode that has a file.
  - `phone_path_for_key(key: str) -> str | None`: a DB lookup only. For a film, `movies.tmdb_id`. For an episode, a join of `episodes` and `shows` on show tmdb, season and episode. When there are duplicate copies, it takes the first by `id`.
  - Routes: `GET /phone/snapshot` → JSON. `GET /phone/file?key=` streams the file, as below. `GET /phone/art/<name>` works like `/art/` in `Handler` (`image/jpeg`, the same `art_filename` guard).
  - **Range behaviour:**
    - no header → 200, the full file, `Accept-Ranges: bytes`;
    - `bytes=a-` or `bytes=a-b` → 206 with `Content-Range: bytes a-b/size`;
    - unparseable, `a ≥ size`, or `b < a` → 416 with `Content-Range: bytes */size`;
    - the file is sent in 1 MiB chunks;
    - `Content-Disposition: attachment; filename="<basename>"`.
  - Unknown key → 404 `{"error": "not in the library"}`. Known key with no file (`media_file_check` false) → 404 `{"error": "the file isn't on the drive"}`.

- [ ] **Step 1: Write the failing tests.** In the sandbox DB, insert a film row (`tmdb_id='999001'`, `path` pointing at a 3 MiB file in `tests/_work`, filled with a byte pattern `bytes(range(256)) * N`) and a show plus episode row (`show tmdb '999002'`, s1e2, a 1 MiB file). Checks:
  - `snapshot has keys`: the film entry carries `key == "m999001"` and `ext == ".mkv"`, and the episode entry carries `key == "e999002s1e2"`
  - `whole file`: GET without Range gives 200, the body equals the file, and `Content-Length` matches
  - `resume from the middle`: `Range: bytes=1048576-` gives 206, the body equals `data[1048576:]`, and the Content-Range is `bytes 1048576-3145727/3145728`
  - `a slice`: `bytes=10-19` gives 206 and 10 bytes
  - `bad ranges are 416`: for each of `bytes=999999999-`, `bytes=abc` and `bytes=5-2`, status 416 and `Content-Range == "bytes */3145728"`
  - `unknown key is 404`: `key=m1`
  - `missing file is 404`: delete the episode's file, and expect 404 with "isn't on the drive"
  - `snapshot needs the token`: no token gives 401
- [ ] **Step 2: Run.** Expect FAIL (404 "no such thing" on `/phone/snapshot`).
- [ ] **Step 3: Implement** the Interfaces. The range parser is `re.fullmatch(r"bytes=(\d+)-(\d*)", header)`.
- [ ] **Step 4: Run.** Expect all checks to pass.
- [ ] **Step 5: Commit:** `"Phone link: snapshot with file keys, ranged downloads"`

### Task 4: Sync exchange

**Files:**
- Modify: `nextup.py` (the phone link section, plus `PhoneHandler` routes)
- Modify: `tests/phone_link_test.py`

**Interfaces:**
- Consumes: `_sync_event_from_row`, `_sync_seed_events(conn, device_id, device)`, `sync_import(conn, folder)`, `sync_apply(conn)`, `sync_dir()`, `sync_device_id()`, `snapshot_device_name()`, `SYNC_KINDS` and `_SYNC_LOCK` (all existing)
- Produces:
  - `PHONE_SYNC_DIR = os.path.join(HERE, "nextup_phone_sync")`. It's redirected by `isolate` in `tests/devserve.py`, and added to `.gitignore` because it's personal history.
  - `phone_events_for(device_id: str) -> str`: jsonl text. It contains this PC's own shareable history rows (`origin IS NULL`, kind in `SYNC_KINDS`, `tmdb_id` set), the seeds from `_sync_seed_events`, and every `sync_inbox.payload` whose `device_id` isn't this phone's. So the phone hears the Mac's events through the PC. It does **not** touch `history.shared`, which belongs to the cloud folder.
  - `phone_receive(device: dict, text: str) -> int`:
    - keeps only lines that are valid JSON with `device_id == device["id"]`;
    - writes them atomically (tmp then `os.replace`) as `device-<id>.jsonl` into `sync_dir(create=True)` if cloud sharing is on (the Mac then gets them through the normal `sync_run`), otherwise into `PHONE_SYNC_DIR`;
    - when it wrote into `PHONE_SYNC_DIR`, runs `sync_import` plus `sync_apply` on it under `_SYNC_LOCK`;
    - returns the number of lines kept.
  - Routes: `GET /phone/sync` → `text/plain; charset=utf-8` jsonl. `POST /phone/sync` with a raw jsonl body (not JSON, so it's read with `Content-Length` directly) → `{"ok": True, "kept": n}`. The body is capped at 20 MB, with 413 above that.

- [ ] **Step 1: Write the failing tests:**
  - `PC events go to the phone`: `log_event("movie", <film id from Task 3>, "Test", "rated", value=8)`, then GET `/phone/sync` contains a line with `"tmdb": "999001"` and `"event": "rated"`
  - `Mac events are relayed`: insert a `sync_inbox` row with `device_id "mac0000000000000"` and that payload, and it appears in GET `/phone/sync`
  - `phone events land on the PC`: POST a line `{"v":1,"uid":"u1","utc":<now>,"device_id":"abcdef0123456789","device":"S24","kind":"movie","tmdb":"999001","event":"rated","value":9,...}`, after which `movies.userrating` for tmdb 999001 is 9 and the response says `kept == 1`
  - `foreign device lines dropped`: a POSTed line claiming `device_id` = `sync_device_id()` (the PC) or `"mac0000000000000"` gives `kept == 0`
  - `oversized upload refused`: a declared `Content-Length` of 21 MB gives 413
  - `cloud folder untouched when sharing is off`: `CONFIG["sync_folder"]` is empty, and `PHONE_SYNC_DIR` holds `device-abcdef0123456789.jsonl`
- [ ] **Step 2: Run.** Expect FAIL.
- [ ] **Step 3: Implement** the Interfaces.
- [ ] **Step 4: Run.** Expect all checks to pass.
- [ ] **Step 5: Commit:** `"Phone link: sync exchange, relaying other devices"`

### Task 5: Being found on the network

**Files:**
- Modify: `nextup.py` (the phone link section)
- Modify: `tests/phone_link_test.py`

**Interfaces:**
- Produces:
  - A UDP responder on port **8790**, started and stopped with the HTTP listener by `phone_link_start`/`phone_link_stop`. It answers the exact datagram `b"NEXTUP?"` with JSON `{"nextup": 1, "pc": snapshot_device_name(), "port": <http port>, "version": APP_VERSION}` sent back to the sender. Anything else is ignored. Only private or loopback senders get an answer.
  - `phone_link_start(port, host, udp_port: int = PHONE_PORT)`, so tests can use 8799.

- [ ] **Step 1: Write the failing tests:**
  - `answers the call`: a UDP socket sends `b"NEXTUP?"` to `127.0.0.1:8799` and receives JSON with `port == 8799` within 2 s
  - `ignores anything else`: `b"hello"` gets no reply within 0.5 s
  - `silent once stopped`: after `phone_link_stop()`, no reply
- [ ] **Step 2: Run.** Expect FAIL (timeout).
- [ ] **Step 3: Implement** it with a daemon thread on a `socket.SOCK_DGRAM` socket with a 1 s timeout loop, checking a stop flag.
- [ ] **Step 4: Run.** Expect all checks to pass.
- [ ] **Step 5: Commit:** `"Phone link: answer discovery on the home network"`

### Task 6: Settings, start-up, and release

**Files:**
- Modify: `nextup.py`: localhost `Handler` routes, a Settings card (HTML, JS and CSS in the `-- settings` facelift block), and start-up in `main()` after `server.serve_forever`
- Modify: `tests/phone_link_test.py`, `tests/run_all.py`, `tests/devserve.py`, `.gitignore`, `README.txt`, `DEVELOPMENT_NOTES.md`

**Interfaces:**
- Consumes: everything above.
- Produces:
  - `phone_link_state() -> dict`: `{"enabled", "port": 8790, "addresses": [this PC's private IPv4s], "pairing": {"code", "left"} | None, "devices": [{"id", "name", "paired_at", "last_seen"}]}`. It never includes tokens or hashes.
  - Localhost routes:
    - `GET /api/phone` → `phone_link_state()`;
    - `POST /api/phone/enable {on: bool}` saves the setting and starts or stops the listener;
    - `POST /api/phone/pair` → `phone_pair_start()`;
    - `POST /api/phone/forget {id}`.
  - `main()` calls `phone_link_start()` if `phone_cfg()["enabled"]`. A bind failure is logged with `log_problem` and shown as `"error"` in the state. It never stops the app starting.
  - A Settings card titled **"Your phone"**:
    - a toggle labelled "Let a phone connect over Wi-Fi";
    - with it on: the PC's address(es) in `<code>`, and a **PAIR A PHONE** button that shows the code large, with a `m:ss` countdown polling `/api/phone` every second while a code is live;
    - a list of paired phones with "last seen" and **FORGET**.
    - Explanatory copy: *"Your phone finds this PC by itself on the same Wi-Fi. Windows may ask whether Python can use private networks — say yes, or the phone can't reach it."*

- [ ] **Step 1: Write the failing tests:**
  - `state hides secrets`: after pairing, `json.dumps(phone_link_state())` contains no token and no `token_sha`
  - `enable toggles the listener`: through the `Handler` routes on a devserve-style `ThreadingHTTPServer` on 8798, POST `/api/phone/enable {"on": true}` makes the 8799 hello answer 401 (it's up), and `{"on": false}` makes the connection refused
  - `page script parses`: the node check from `tests/youtube_test.py`
- [ ] **Step 2: Run.** Expect FAIL.
- [ ] **Step 3: Implement.** The routes call `phone_link_start(PHONE_PORT)` by default. In tests, set `n.PHONE_PORT = 8799` before anything starts.
- [ ] **Step 4: Run** `python tests\phone_link_test.py`. Expect all checks to pass.
- [ ] **Step 5: Check it in the browser.** Start `nextup-dev`, open Settings, turn the toggle on, press PAIR A PHONE, then measure that the code shows, the countdown moves and FORGET works. Take a screenshot. With the queue docked and at 760 px, check that the card doesn't overflow. Turn it off again.
- [ ] **Step 6: Register and release:**
  - add `("phone link", "phone_link_test.py")` to `tests/run_all.py`;
  - `isolate()` redirects `PHONE_SYNC_DIR` and forces `phone_link` off in the copied config;
  - add `nextup_phone_sync/` to `.gitignore`;
  - bump `APP_VERSION` and README to 0.1.48 (with no BOM: use `sed`, not PowerShell `Set-Content`);
  - write the notes entry;
  - run `python tests\run_all.py` and expect all suites to pass.
- [ ] **Step 7: Commit:** `"v0.1.48: the phone link (PC side)"`
