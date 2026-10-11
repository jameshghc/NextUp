"""The PC half of wifi_stream_test's history swap, in a process of its own so
that it has a database of its own: a sandbox copy, its phone link on a test
port, the test phone paired. Prints the phone's token, then answers one
command per line on stdin:

    rate <tmdb> <value>   log a rating here, as you would on the PC
    has <uid>             1 if an event with that uid has arrived here, else 0
    inbox                 how many events have arrived from other devices
    film <tmdb> <resume>  a real film file here, with this PC's watch point
    episode <tmdb> <s> <e>  a real episode file of that show here
    asleep 1|0            the drive stops (or starts) answering
    quit
"""
import sys, os, tempfile
ARGS = sys.argv[1:]
sys.path.insert(0, r"X:\NextUp"); os.chdir(r"X:\NextUp"); sys.argv = ["nextup.py"]
import nextup as n
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from devserve import isolate

port, phone = int(ARGS[0]), ARGS[1]
isolate(n, os.path.join(tempfile.gettempdir(), "nextup_wifistream_pc"))
REAL_CHECK = n.media_file_check
n.phone_link_start(port, "127.0.0.1")
print(n.phone_pair_direct(phone, "Test Phone"), flush=True)
for line in sys.stdin:
    cmd = line.split()
    if not cmd:
        continue
    if cmd[0] == "quit":
        break
    conn = n.db()
    try:
        if cmd[0] == "rate":
            row = conn.execute("SELECT id, title FROM movies WHERE tmdb_id=? LIMIT 1", (cmd[1],)).fetchone()
            if row is None:
                cur = conn.execute("INSERT INTO movies (path,title,year,tmdb_id) VALUES (?,?,?,?)",
                                   (os.path.join(tempfile.gettempdir(), "pc-%s.mkv" % cmd[1]),
                                    "PC Film", 2021, cmd[1]))
                conn.commit()
                row = {"id": cur.lastrowid, "title": "PC Film"}
            conn.close(); conn = None
            n.log_event("movie", row["id"], row["title"], "rated", value=float(cmd[2]))
            print("ok", flush=True)
        elif cmd[0] == "has":
            got = conn.execute("SELECT 1 FROM sync_inbox WHERE uid=?", (cmd[1],)).fetchone()
            print("1" if got else "0", flush=True)
        elif cmd[0] == "film":
            path = os.path.join(tempfile.gettempdir(), "nextup_wifistream_pc", "pc-film-%s.mkv" % cmd[1])
            open(path, "wb").write(b"F" * 50000)
            conn.execute("INSERT INTO movies (path,title,year,tmdb_id,resume_pos,resume_total)"
                         " VALUES (?,?,?,?,?,?)", (path, "PC Only Film", 2019, cmd[1], int(cmd[2]), 6000))
            conn.commit()
            print("ok", flush=True)
        elif cmd[0] == "episode":
            path = os.path.join(tempfile.gettempdir(), "nextup_wifistream_pc",
                                "pc-ep-%s-%s-%s.mkv" % tuple(cmd[1:4]))
            open(path, "wb").write(b"P" * 40000)
            show = conn.execute("SELECT id FROM shows WHERE tmdb_id=?", (cmd[1],)).fetchone()
            show_id = show[0] if show else conn.execute(
                "INSERT INTO shows (name,title,tmdb_id) VALUES (?,?,?)",
                ("pc show", "PC Only Show", cmd[1])).lastrowid
            conn.execute("INSERT INTO episodes (path,show_id,season,episode) VALUES (?,?,?,?)",
                         (path, show_id, int(cmd[2]), int(cmd[3])))
            conn.commit()
            print("ok", flush=True)
        elif cmd[0] == "asleep":
            n.media_file_check = (lambda p: None) if cmd[1] == "1" else REAL_CHECK
            print("ok", flush=True)
        elif cmd[0] == "inbox":
            print(conn.execute("SELECT COUNT(*) FROM sync_inbox").fetchone()[0], flush=True)
    finally:
        if conn is not None:
            conn.close()
n.phone_link_stop()
