"""The phone draws on the PC's library: the PC's Now, genres and Channels as
the paired phone sees them, the phone's passthrough and play-here, and the
page. Against a sandbox copy (devserve.isolate), loopback ports 8788/8789."""
import sys, os, re, json, time, tempfile, threading, urllib.request, urllib.error
sys.path.insert(0, r"X:\NextUp"); os.chdir(r"X:\NextUp"); sys.argv = ["nextup.py"]
import nextup as n
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from devserve import isolate
isolate(n, os.path.join(tempfile.gettempdir(), "nextup_pclib"))

results = []
def check(name, ok, detail=""):
    ok = bool(ok); results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- %s" % (detail,)) if detail != "" else ""))

PHONE = "aaaabbbbccccdddd"
PORT = 8789
n.phone_link_start(PORT, "127.0.0.1")
token = n.phone_pair_direct(PHONE, "S21")
def call(path, tok=token):
    req = urllib.request.Request("http://127.0.0.1:%d%s" % (PORT, path))
    if tok:
        req.add_header("Authorization", "Bearer " + tok)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, {}

# --- Task 1: the PC's routes -----------------------------------------------------------
check("the PC's lists need the token", call("/phone/now", tok=None)[0] == 401
      and call("/phone/channels", tok=None)[0] == 401)
st, now = call("/phone/now?kind=film&mood=any&count=6")
picks = now.get("picks") or []
check("Now over the wire: picks, each knowing what it is", st == 200 and picks
      and all(p.get("ident", {}).get("kind") == "movie" and p["ident"].get("tmdb") for p in picks if p.get("ident"))
      and sum(1 for p in picks if p.get("ident")) >= 1, [(p.get("title"), p.get("ident")) for p in picks[:3]])
check("film means films", all(p.get("type") == "movie" for p in picks), [p.get("type") for p in picks])
check("pictures the phone can fetch", all(not p.get("art") or p["art"].startswith("/phone/art/") for p in picks),
      [p.get("art") for p in picks[:2]])
cont = now.get("continue") or []
check("Continue comes with it, each item knowing what it is", cont and all("ident" in c for c in cont),
      [(c.get("title"), c.get("ident")) for c in cont[:2]])
check("an episode's identity has its season and episode",
      all(c["ident"] is None or c["ident"]["kind"] != "episode" or
          (c["ident"].get("season") is not None and c["ident"].get("episode") is not None) for c in cont))
conn = n.db()
cur = conn.execute("INSERT INTO movies (path,title,year) VALUES ('X:/nope/unknown.mkv','Unknown Thing',2001)")
unknown = cur.lastrowid
conn.commit(); conn.close()
check("something with no TMDB id has no identity (ON PC only)", n.ident_for("movie", unknown) is None)
st, g = call("/phone/genres?kind=film&with=")
check("genres as the PC counts them", st == 200 and g.get("genres") == n.available_genres("film", []),
      (g.get("genres") or [])[:3])
st, ch = call("/phone/channels")
chans = ch.get("channels") or []
check("channels over the wire, with how far in", st == 200 and chans
      and all(c.get("live") or c.get("now") is None or c["now"].get("offset", -1) >= 0 for c in chans),
      [(c.get("name"), (c.get("now") or {}).get("offset")) for c in chans[:3]])
check("a live channel has no identity: ON PC only",
      all(not (c.get("now") or {}).get("ident") for c in chans if c.get("live") or c.get("youtube")))
check("a film or episode channel says what to play",
      any((c.get("now") or {}).get("ident") for c in chans if not c.get("live") and not c.get("youtube")))
# A two-episode block, twenty minutes past the end of the first episode:
conn = n.db()
eps = conn.execute("SELECT e.id, e.runtime FROM episodes e JOIN shows s ON s.id=e.show_id"
                   " WHERE s.tmdb_id<>'' AND e.season>0 ORDER BY e.show_id, e.season, e.episode LIMIT 2").fetchall()
conn.close()
first = eps[0]["runtime"] or n.DEFAULT_EPISODE_RUNTIME
ident, at = n.channel_ident({"kind": "episodes", "episode_ids": [eps[0]["id"], eps[1]["id"]]}, first + 1200)
want = n.ident_for("episode", eps[1]["id"])
check("two episodes in a block: the one playing now, and how far into it", ident == want and at == 1200, (ident, at, want))

# The rest of the suite (tasks 2 and 3) appends below this line.

# --- Task 2: the phone's side ----------------------------------------------------------
# This process plays the phone now, reaching the PC half above on loopback.
n.PLATFORM = "android"
n.CONFIG["device_id"] = PHONE
n.CONFIG["pc_link"] = {"token": token, "pc": "Test PC", "pc_id": "", "port": PORT,
                       "addresses": ["127.0.0.1"], "last_ip": None}
n.pc_link_check(force=True)
desk = n.ThreadingHTTPServer(("127.0.0.1", 8788), n.Handler)
threading.Thread(target=desk.serve_forever, daemon=True).start()
def dget(path):
    with urllib.request.urlopen("http://127.0.0.1:8788" + path, timeout=30) as r:
        return json.loads(r.read())
def dpost(path, body):
    req = urllib.request.Request("http://127.0.0.1:8788" + path, data=json.dumps(body).encode(), method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())
got = dget("/api/pcnow?kind=film&count=4")
check("the phone passes the PC's Now through", got.get("picks")
      and all(not p.get("art") or p["art"].startswith("/api/pcremote/art/") for p in got["picks"]),
      [p.get("art") for p in (got.get("picks") or [])[:2]])
check("and its genres", dget("/api/pcgenres?kind=film").get("genres"))
check("and its channels", dget("/api/pcchannels").get("channels"))

played = []
n.ANDROID_PLAYER = lambda path, start, subs=None: played.append((path, int(start)))
n.require_media_file = lambda path: path
conn = n.db()
local = conn.execute("SELECT id, tmdb_id, path FROM movies WHERE tmdb_id<>'' AND path IS NOT NULL LIMIT 1").fetchone()
conn.close()
r = dpost("/api/play", {"stream": {"kind": "movie", "tmdb": local["tmdb_id"]}, "start": 125})
check("HERE plays the phone's own copy when it has one, not a stream", played and played[-1][0] == local["path"],
      (r, played[-1:]))
check("and starts where it was asked to", played and played[-1][1] == 125, played[-1:])

carried = []
n._carry_on_soon = lambda chan: carried.append(chan)
n._ANDROID_SITTING.update(channel="cult", started_at=time.time() - 3000)
n.android_play_finished(completed=True)
check("a channel watched here carries on when its programme ends", carried == ["cult"], carried)
carried.clear()
dpost("/api/play", {"stream": {"kind": "movie", "tmdb": local["tmdb_id"]}, "start": 0, "channel": "cult"})
check("the channel is kept with the sitting", n._ANDROID_SITTING.get("channel") == "cult", dict(n._ANDROID_SITTING))
n.android_play_finished(position=600, duration=6000)
check("stopping by hand ends the channel", carried == [], carried)

n.phone_link_stop()
n.PC_LINK.update(checked=0)
got = dget("/api/pcnow?kind=film")
check("PC away: said plainly, nothing thrown", got.get("error") == n.PC_AWAY, got)
desk.shutdown()
n.PLATFORM = "windows"
n.phone_link_stop()
print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
