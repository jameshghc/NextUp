"""Two computers, one cloud folder. Every check prints PASS/FAIL."""
import os, sys, json, time, shutil, sqlite3, subprocess, urllib.request, hashlib, py_compile

HERE = os.path.dirname(os.path.abspath(__file__))
# The two pretend computers hold copies of the real library AND config -
# private, and never to be committed. They live under tests\_work.
WORK = os.path.join(os.path.dirname(HERE), "_work", "synctest")
os.makedirs(WORK, exist_ok=True)
LIVE = r"X:\NextUp"
CLOUD = os.path.join(WORK, "cloud")
STAGES = {"A": (os.path.join(WORK, "A"), 8773, "PC-TEST"),
          "B": (os.path.join(WORK, "B"), 8774, "MAC-TEST")}
results = []


def check(name, ok, detail=""):
    ok = bool(ok)
    results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  — " + str(detail)) if detail else ""), flush=True)


py_compile.compile(os.path.join(LIVE, "nextup.py"), doraise=True)
for d in [CLOUD] + [s[0] for s in STAGES.values()]:
    if os.path.isdir(d):
        shutil.rmtree(d)
os.makedirs(CLOUD)
for key, (stage, port, name) in STAGES.items():
    os.makedirs(stage)
    shutil.copy2(os.path.join(LIVE, "nextup.py"), stage)
    shutil.copy2(os.path.join(LIVE, "nextup_library.db"), stage)
    shutil.copytree(os.path.join(LIVE, "nextup_resume"), os.path.join(stage, "nextup_resume"))
    cfg = json.load(open(os.path.join(LIVE, "nextup_config.json"), encoding="utf-8"))
    cfg.update(device_name=name, sync_folder="", device_id="", sync_offer_dismissed=False)
    json.dump(cfg, open(os.path.join(stage, "nextup_config.json"), "w", encoding="utf-8"))

# Two real computers never share history uids. Two copies of one library
# do — every row already carries the uid it was shared under — so B's copy
# forgets them, the way a separate machine's history never had them.
cb = sqlite3.connect(os.path.join(STAGES["B"][0], "nextup_library.db"))
cb.execute("UPDATE history SET uid=NULL, shared=NULL, origin=NULL")
cb.execute("DELETE FROM sync_inbox"); cb.execute("DELETE FROM sync_files"); cb.execute("DELETE FROM sync_devices")
cb.commit(); cb.close()
ca = sqlite3.connect(os.path.join(STAGES["A"][0], "nextup_library.db"))
ca.execute("DELETE FROM sync_inbox"); ca.execute("DELETE FROM sync_files"); ca.execute("DELETE FROM sync_devices")
ca.commit(); ca.close()

procs = [subprocess.Popen([sys.executable, os.path.join(HERE, "runner.py"), s, str(p)],
                          stdout=open(os.path.join(s + ".log"), "w"), stderr=subprocess.STDOUT)
         for s, p, _ in STAGES.values()]


def call(key, path, body=None):
    port = STAGES[key][1]
    req = urllib.request.Request("http://127.0.0.1:%d%s" % (port, path),
                                 data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def q(key, sql, args=()):
    c = sqlite3.connect(os.path.join(STAGES[key][0], "nextup_library.db"))
    c.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in c.execute(sql, args)]
    finally:
        c.close()


def sync_both(rounds=2):
    for _ in range(rounds):
        call("A", "/api/sync/now", {})
        call("B", "/api/sync/now", {})


try:
    for _ in range(60):
        try:
            call("A", "/api/status"); call("B", "/api/status"); break
        except Exception:
            time.sleep(0.5)

    s = call("A", "/api/sync/status")
    check("offer shown before setup (real OneDrive detected)", s["offer"] and s["detected"], s["detected"])
    before = {r["id"]: r["userrating"] for r in q("A", "SELECT id,userrating FROM movies")}

    t = time.time()
    a = call("A", "/api/sync/enable", {"folder": CLOUD})
    b = call("B", "/api/sync/enable", {"folder": CLOUD})
    check("enable on both", a["enabled"] and b["enabled"] and not a["error"] and not b["error"],
          "%.1fs" % (time.time() - t))
    sync_both()
    files = sorted(os.listdir(os.path.join(CLOUD, "Next Up sync")))
    check("each computer has exactly its own file", len(files) == 2, files)
    sa, sb = call("A", "/api/sync/status"), call("B", "/api/sync/status")
    check("A hears from MAC-TEST", [d["name"] for d in sa["devices"]] == ["MAC-TEST"], sa["devices"])
    check("B hears from PC-TEST", [d["name"] for d in sb["devices"]] == ["PC-TEST"], sb["devices"])
    after = {r["id"]: r["userrating"] for r in q("A", "SELECT id,userrating FROM movies")}
    check("identical libraries: sharing changed no rating", before == after,
          sum(1 for k in before if before[k] != after.get(k)))
    hist_rows = q("A", "SELECT COUNT(*) n FROM history WHERE origin IS NOT NULL")[0]["n"]
    check("B's history arrived on A as rows marked with its device", hist_rows > 500, hist_rows)

    # --- ratings: A rates, B follows -----------------------------------------
    film = q("A", "SELECT id,title,tmdb_id FROM movies WHERE userrating=0 AND tmdb_id<>'' LIMIT 1")[0]
    call("A", "/api/rate", {"type": "movie", "id": film["id"], "rating": 7})
    time.sleep(1.1)
    sync_both()
    got = q("B", "SELECT userrating FROM movies WHERE tmdb_id=?", (film["tmdb_id"],))
    check("rating on A reaches B (%s)" % film["title"], all(r["userrating"] == 7 for r in got), got)

    # --- conflict: later wins, on both --------------------------------------
    call("A", "/api/rate", {"type": "movie", "id": film["id"], "rating": 5})
    time.sleep(1.1)
    call("B", "/api/rate", {"type": "movie", "id": film["id"], "rating": 9})
    sync_both(3)
    ra = q("A", "SELECT userrating FROM movies WHERE id=?", (film["id"],))[0]["userrating"]
    rb = q("B", "SELECT userrating FROM movies WHERE id=?", (film["id"],))[0]["userrating"]
    check("two computers rate the same film: the later (9) wins on both", ra == 9 and rb == 9, (ra, rb))

    # --- clearing a rating is an event too -----------------------------------
    time.sleep(1.1)
    call("B", "/api/rate", {"type": "movie", "id": film["id"], "rating": 0})
    sync_both()
    ra = q("A", "SELECT userrating,rated_at FROM movies WHERE id=?", (film["id"],))[0]
    check("clearing a rating on B clears it on A", ra["userrating"] == 0 and ra["rated_at"] is None, ra)

    # --- watchlist + favourite: B toggles, A follows --------------------------
    other = q("B", "SELECT id,tmdb_id,title FROM movies WHERE watchlisted_at IS NULL"
                   " AND favourited_at IS NULL AND tmdb_id<>'' LIMIT 1 OFFSET 20")[0]
    call("B", "/api/watchlist", {"type": "movie", "id": other["id"]})
    call("B", "/api/favourite", {"type": "movie", "id": other["id"]})
    sync_both()
    r = q("A", "SELECT watchlisted_at,favourited_at FROM movies WHERE id=?", (other["id"],))[0]
    check("watchlist + favourite on B reach A (%s)" % other["title"],
          bool(r["watchlisted_at"]) and bool(r["favourited_at"]), r)
    time.sleep(1.1)
    call("A", "/api/watchlist", {"type": "movie", "id": other["id"]})
    sync_both()
    r = q("B", "SELECT watchlisted_at FROM movies WHERE id=?", (other["id"],))[0]
    check("removing it from the watchlist on A removes it on B", r["watchlisted_at"] is None, r)

    # --- resume position: stop on B, resume on A -----------------------------
    m = q("A", "SELECT id,title,path,tmdb_id,playcount FROM movies WHERE resume_pos=0"
               " AND tmdb_id<>'' LIMIT 1 OFFSET 40")[0]
    call("B", "/test/played", {"kind": "movie", "id": m["id"]})
    time.sleep(1.1)
    call("B", "/test/stop", {"kind": "movie", "id": m["id"], "position": 2419, "total": 6900})
    sync_both()
    r = q("A", "SELECT resume_pos,resume_total,playcount FROM movies WHERE id=?", (m["id"],))[0]
    check("stopped at 40:19 on B -> A resumes there (%s)" % m["title"],
          int(r["resume_pos"]) == 2419 and r["playcount"] == m["playcount"], r)
    wl = os.path.join(STAGES["A"][0], "nextup_resume",
                      hashlib.md5(m["path"].encode("utf-8")).hexdigest().upper())
    check("mpv's own resume file written on A", os.path.isfile(wl) and "start=2419" in open(wl).read())
    # the trap: sync_playback_state must not turn that into a play
    call("A", "/api/browse")
    call("A", "/api/status")
    r = q("A", "SELECT resume_pos,playcount FROM movies WHERE id=?", (m["id"],))[0]
    check("A's resume-folder check didn't mistake it for a finished film",
          int(r["resume_pos"]) == 2419 and r["playcount"] == m["playcount"], r)
    cont = call("A", "/api/resume")
    check("it's in Continue where you left off on A",
          any(i.get("id") == m["id"] for i in cont["items"]), [i.get("title") for i in cont["items"]][:4])

    # --- finish it on A: B's position clears, playcount goes up ---------------
    time.sleep(1.1)
    call("A", "/test/watched", {"kind": "movie", "id": m["id"], "total": 6900})
    sync_both()
    r = q("B", "SELECT resume_pos,playcount FROM movies WHERE id=?", (m["id"],))[0]
    check("finished on A -> B's resume point clears and it counts a play",
          r["resume_pos"] == 0 and r["playcount"] == m["playcount"] + 1, r)

    # --- History shows the other computer's sittings --------------------------
    h = call("A", "/api/history")
    row = next((i for i in h["items"] if i["kind"] == "movie" and i["id"] == m["id"]), None)
    devs = sorted(set(str(s.get("device")) for s in row["sessions"])) if row else None
    check("History on A: one row, sittings from both computers", row is not None and "MAC-TEST" in devs and "None" in devs, devs)

    # --- something A doesn't own --------------------------------------------
    own_b = [f for f in os.listdir(os.path.join(CLOUD, "Next Up sync"))
             if f == "device-%s.jsonl" % json.load(open(os.path.join(STAGES["B"][0], "nextup_config.json")))["device_id"]][0]
    path_b = os.path.join(CLOUD, "Next Up sync", own_b)
    b_id = own_b[7:-6]
    ghost = {"v": 1, "uid": "ghost-1", "utc": time.time(), "device_id": b_id, "device": "MAC-TEST",
             "kind": "movie", "tmdb": "999999991", "season": None, "episode": None, "show": None,
             "title": "A Film Only The Mac Has", "event": "watched", "value": None,
             "seconds": 5000, "position": 5400, "total": 5400}
    line = json.dumps(ghost) + "\n"
    with open(path_b, "a", encoding="utf-8") as fh:
        fh.write(line[:40])                      # half a line, as a sync mid-copy
    call("A", "/api/sync/now", {})
    check("half-written line is left for next time, no error",
          not q("A", "SELECT 1 FROM sync_inbox WHERE uid='ghost-1'") and not call("A", "/api/sync/status")["error"])
    with open(path_b, "a", encoding="utf-8") as fh:
        fh.write(line[40:])
    call("A", "/api/sync/now", {})
    h = call("A", "/api/history")
    g = next((i for i in h["items"] if i["title"] == "A Film Only The Mac Has"), None)
    check("a film only the Mac has appears in A's History, unplayable, marked",
          g is not None and not g["available"] and g["device"] == "MAC-TEST", g and {k: g[k] for k in ("available", "device", "finished")})
    check("and waits in the inbox for a scan", call("A", "/api/sync/status")["waiting"] >= 1)

    # --- no echo: repeated rounds add nothing --------------------------------
    sizes = [os.path.getsize(os.path.join(CLOUD, "Next Up sync", f)) for f in sorted(os.listdir(os.path.join(CLOUD, "Next Up sync")))]
    sync_both(3)
    time.sleep(4)
    sizes2 = [os.path.getsize(os.path.join(CLOUD, "Next Up sync", f)) for f in sorted(os.listdir(os.path.join(CLOUD, "Next Up sync")))]
    check("no echo: six more rounds, files unchanged", sizes == sizes2, (sizes, sizes2))
    dup = q("A", "SELECT uid, COUNT(*) n FROM history WHERE uid IS NOT NULL GROUP BY uid HAVING n>1")
    check("no duplicate history rows", not dup, dup[:3])

    # --- a deleted file heals itself -----------------------------------------
    own_a = "device-%s.jsonl" % json.load(open(os.path.join(STAGES["A"][0], "nextup_config.json")))["device_id"]
    before_a = os.path.getsize(os.path.join(CLOUD, "Next Up sync", own_a))
    os.remove(os.path.join(CLOUD, "Next Up sync", own_a))
    sync_both()
    after_a = os.path.getsize(os.path.join(CLOUD, "Next Up sync", own_a))
    hist_b_before = hist_rows
    dup = q("B", "SELECT uid, COUNT(*) n FROM history WHERE uid IS NOT NULL GROUP BY uid HAVING n>1")
    check("A's file deleted -> rewritten whole, B takes no duplicates",
          after_a >= before_a and not dup, (before_a, after_a))

    # --- page and history still render -------------------------------------
    page = urllib.request.urlopen("http://127.0.0.1:8773/", timeout=30).read().decode("utf-8")
    import re
    js = "\n;\n".join(re.findall(r"<script>(.*?)</script>", page, re.S))
    open(os.path.join(WORK, "page.js"), "w", encoding="utf-8").write(js)
    node = subprocess.run(["node", "-e", "new Function(require('fs').readFileSync(process.argv[1],'utf8'));console.log('ok')",
                           os.path.join(WORK, "page.js")], capture_output=True, text=True)
    check("page script parses", node.stdout.strip() == "ok", node.stderr[:300])

    t = time.time(); call("A", "/api/history"); dt = time.time() - t
    check("history still quick with both computers' rows", dt < 2, "%.2fs" % dt)

    call("B", "/api/sync/disable", {})
    check("stop sharing leaves the cloud files alone", len(os.listdir(os.path.join(CLOUD, "Next Up sync"))) == 2)
finally:
    for p in procs:
        p.terminate()
    print("\n%d/%d passed" % (sum(results), len(results)))
    for key, (stage, _, _) in STAGES.items():
        log = open(stage + ".log").read()
        if "Traceback" in log:
            print("---", key, "log ---\n", log[-2000:])
