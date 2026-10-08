"""devserve as the phone: Next Up in its Android mode, for trying the phone
app's behaviour in a browser without a phone. Open it at phone width.

What's the same as on the phone: PLATFORM is "android", so every path the
app takes on the phone is the one taken here — play handed to "mpv" rather
than a desktop player, no player monitor, the phone layout's rules.

The library is built the way a phone's really is: a handful of films and a
show the phone found in its own folder (unrated, unwatched — a fresh scan),
plus your whole PC library sent over as a snapshot, greyed where it isn't
here. The local files are small stand-ins in a temp folder, never the real
films on E:.

"mpv" is pretend: it prints what it was handed, and three seconds later
closes as though you'd watched five minutes and backed out — so resume
points can be tried end to end.

What it can't show: Android itself — the permission prompt, the media
index, the real mpv app, the WebView's quirks. A real phone is still the
last word on those."""
import os, sys, tempfile, threading
# Decided when nextup is imported, as on the phone.
os.environ["NEXTUP_PLATFORM"] = "android"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import devserve, nextup as n
from http.server import ThreadingHTTPServer

PORT = 8776
assert n.PLATFORM == "android", n.PLATFORM
devserve.isolate(n, os.path.join(tempfile.gettempdir(), "nextup_phone_serve"))
PHONE = os.path.join(tempfile.gettempdir(), "nextup_phone_serve", "Film & TV")

# The PC's catalogue, as SEND MY LIBRARY would carry it.
snapshot = n.build_library_snapshot()

# What the phone found in its own folder: these, and nothing else.
ON_PHONE = ("Akira", "Aladdin", "Dune", "Parasite")
SHOW = "Pantheon"
conn = n.db()
keep = []
for name in ON_PHONE:
    row = conn.execute("SELECT id, title, year, path FROM movies WHERE title LIKE ? AND tmdb_id <> ''"
                       " ORDER BY id LIMIT 1", (name + "%",)).fetchone()
    if row:
        keep.append(row)
if not keep:
    keep = conn.execute("SELECT id, title, year, path FROM movies WHERE tmdb_id <> '' LIMIT 4").fetchall()
show = conn.execute("SELECT id, title FROM shows WHERE title LIKE ? LIMIT 1", (SHOW + "%",)).fetchone()

conn.execute("DELETE FROM movies WHERE id NOT IN (%s)" % ",".join(str(r["id"]) for r in keep))
conn.execute("DELETE FROM shows WHERE id <> ?", (show["id"] if show else -1,))
conn.execute("DELETE FROM episodes WHERE show_id <> ?", (show["id"] if show else -1,))
fresh = ("userrating=0, rated_at=NULL, playcount=0, resume_pos=0, resume_total=0,"
         " last_played=NULL, watchlisted_at=NULL, favourited_at=NULL")
os.makedirs(os.path.join(PHONE, "Films"), exist_ok=True)
for r in keep:
    stand_in = os.path.join(PHONE, "Films", os.path.basename(r["path"]))
    open(stand_in, "wb").close()
    conn.execute("UPDATE movies SET path=?, %s WHERE id=?" % fresh, (stand_in, r["id"]))
if show:
    conn.execute("UPDATE shows SET userrating=0, rated_at=NULL, watchlisted_at=NULL,"
                 " favourited_at=NULL WHERE id=?", (show["id"],))
    for e in conn.execute("SELECT id, path FROM episodes WHERE show_id=?", (show["id"],)).fetchall():
        stand_in = os.path.join(PHONE, "TV", show["title"], os.path.basename(e["path"] or "%d.mkv" % e["id"]))
        os.makedirs(os.path.dirname(stand_in), exist_ok=True)
        open(stand_in, "wb").close()
        conn.execute("UPDATE episodes SET path=?, playcount=0, resume_pos=0, resume_total=0,"
                     " last_played=NULL WHERE id=?", (stand_in, e["id"]))
conn.commit(); conn.close()
n.CONFIG["media_folders"] = [PHONE]
n.LOCAL.loaded_at = 0; n.LIB.loaded_at = 0

# And the PC's library arriving, as it does on the phone.
got = n.import_library_snapshot(snapshot, fetch_art=False)

n.ANDROID_VIDEO_ACCESS = lambda: True


def pretend_mpv(path, start):
    print("[mpv] opened %s at %ds" % (os.path.basename(path), start), flush=True)
    stopped = start + 300

    def close():
        print("[mpv] closed at %ds" % stopped, flush=True)
        n.android_play_finished(position=stopped, duration=max(stopped * 2, 7200))
    threading.Timer(3, close).start()
n.ANDROID_PLAYER = pretend_mpv

n.prepare_app()
print("phone serve on http://127.0.0.1:%d — %d films and %s on the phone, %d films and %d shows sent "
      "from the PC, %d ratings carried onto the phone's own" % (
          PORT, len(keep), show["title"] if show else "no show", got["movies"], got["shows"],
          got.get("marks", 0)), flush=True)
ThreadingHTTPServer(("127.0.0.1", PORT), n.Handler).serve_forever()
