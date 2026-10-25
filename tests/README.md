# Tests

Run them all — about a minute:

```
python tests\run_all.py
```

`python tests\run_all.py quick` skips the two-computer sharing test.

## The one rule

**A test never touches your real files.** Every suite imports `devserve.py`
and calls `isolate()`, which points every file the app writes — the library,
config, recommendations, the now-playing state, resume points, the error log
— at a sandbox copy in the system temp folder, and refuses to start if any of
them still points into `X:\NextUp`. `run_all.py` fingerprints the real files
before and after as a second check.

That rule exists because it was once broken: a browser test saved a blank
over the real `nextup_config.json` and switched sharing off for four days.

The sorter suites also build a fake downloads folder and check that the real
`E:\Torrents` is exactly as it was afterwards.

## The suites

`run_all.py` lists all of them (about twenty-five); a few of the older ones:

| | checks | what it proves |
|---|---|---|
| `queue_test.py` | 19 | the queue hands over only when something ENDS, never when you close it |
| `afk_test.py` | 61 | "are you still watching?" — bands, idle detection, holding and resuming a hand-over |
| `port_test.py` | 10 | the port frees at once on close, and a second copy waits instead of refusing |
| `port_e2e.py` | 5 | the same, through the app's real startup and shutdown |
| `sorter_test.py` | 16 | SORT NEW DOWNLOADS: preview changes nothing, the run moves files, titles come from TMDB |
| `dupes_test.py` | 24 | a duplicate download: the better copy wins, nothing is deleted, the bin waits for you |
| `synctest/driver.py` | 27 | sharing between computers — two copies of the app and a fake cloud folder |

## Tools, not tests

| | |
|---|---|
| `devserve.py` | the app's server on port 8771, sandboxed — for trying the page in a browser |
| `afk_serve.py` | the same with the "still watching?" question already up (8772) |
| `aside_serve.py` | the same with duplicate copies waiting to be binned (8773); run `dupes_test.py` with `STOP_BEFORE_BIN=1` first |
| `pick_audit_v2.py` | 3,000 presses of "Pick something": who comes up, how often, what never does |
| `pick_check.py` | the show cooldown and where watchlisted films sit in the draw |
| `recent_ep_check.py` | which episode each show would offer, old rule against new |
| `tidy_audit.py` | dead CSS and unused functions in `nextup.py` |

Run a pick audit before and after changing any of the picking numbers.

## `_work`

Scratch output: fake download folders, page-script checks, and the sync
test's two pretend computers — which hold **copies of your real library and
config, passwords included**. It is safe to delete and is never to be shared
or committed.
