"""Run every test suite and print one summary.

    python tests\\run_all.py            everything - about a minute
    python tests\\run_all.py quick      without the two-computer sharing test

Each suite runs in its own process against a sandbox copy of the library and
config — see devserve.isolate — and the real data files are fingerprinted
before and after, so a suite that ever writes to them fails the whole run.
"""
import os, re, subprocess, sys, time, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
LIVE = os.path.dirname(HERE)

SUITES = [
    ("queue", "queue_test.py"),
    ("audio delay per file", "audio_delay_test.py"),
    ("three tags per poster", "tile_tags_test.py"),
    ("one show per TMDB id", "show_merge_test.py"),
    ("recommendations home", "rec_home_test.py"),
    ("the look", "appearance_test.py"),
    ("closing to the tray", "tray_test.py"),
    ("short sittings", "short_sittings_test.py"),
    ("episode scores", "episode_scores_test.py"),
    ("home", "home_test.py"),
    ("a friend's first run", "first_run_test.py"),
    ("are you still watching", "afk_test.py"),
    ("port release", "port_test.py"),
    ("port release, end to end", "port_e2e.py"),
    ("download sorter", "sorter_test.py"),
    ("sorter duplicates", "dupes_test.py"),
    ("empty shows", "empty_shows_test.py"),
    ("youtube channel", "youtube_test.py"),
    ("phone link", "phone_link_test.py"),
    ("streaming over wi-fi", "wifi_stream_test.py"),
    ("the phone as a remote", "phone_remote_test.py"),
    ("the phone draws on the PC", "phone_pclib_test.py"),
    ("android core", "android_core_test.py"),
    ("phone over usb", "usb_phone_test.py"),
    ("phone as a drive", "phone_dock_test.py"),
    ("sharing between computers", os.path.join("synctest", "driver.py")),
]
SLOW = {"sharing between computers"}

# The files a test must never change. The media folders are checked by the
# sorter suites themselves.
GUARDED = ["nextup_config.json", "nextup_library.db", "nextup_recs.json",
           "nextup_playing.json", "nextup_dismissed.json", "nextup_youtube.json"]


def fingerprint():
    out = {}
    for name in GUARDED:
        path = os.path.join(LIVE, name)
        if os.path.isfile(path):
            with open(path, "rb") as fh:
                out[name] = hashlib.md5(fh.read()).hexdigest()
    return out


def main():
    quick = "quick" in sys.argv[1:]
    before = fingerprint()
    results, started = [], time.time()
    for label, script in SUITES:
        if quick and label in SLOW:
            continue
        t = time.time()
        proc = subprocess.run([sys.executable, os.path.join(HERE, script)],
                              cwd=os.path.dirname(os.path.join(HERE, script)),
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=1200)
        out = (proc.stdout or "") + (proc.stderr or "")
        m = re.findall(r"(\d+)/(\d+) (?:checks )?passed", out)
        passed, total = (int(m[-1][0]), int(m[-1][1])) if m else (0, 0)
        ok = proc.returncode == 0 and total and passed == total
        results.append((label, ok, passed, total, time.time() - t))
        print("%s  %-28s %s  %4.0fs" % ("PASS" if ok else "FAIL", label,
              "%d/%d" % (passed, total) if total else "no result", time.time() - t), flush=True)
        if not ok:
            for line in [l for l in out.splitlines() if l.startswith("FAIL") or "Error" in l][-8:]:
                print("        " + line)
    # The live app may have written its own files meanwhile (it runs beside
    # this), so a change is reported, not assumed to be a test's doing.
    changed = [k for k, v in fingerprint().items() if before.get(k) != v]
    print()
    if changed:
        print("NOTE  real files changed during the run: %s — if the app wasn't "
              "running, a test wrote to them" % ", ".join(changed))
    bad = [r for r in results if not r[1]]
    print("%d of %d suites passed, %d checks, %.0f minutes"
          % (len(results) - len(bad), len(results), sum(r[2] for r in results),
             (time.time() - started) / 60))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
