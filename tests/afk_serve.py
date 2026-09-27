# -*- coding: utf-8 -*-
"""devserve, but with the "are you still watching?" question already up, so
the overlay can be looked at without waiting four hours for one. Sandboxed
exactly as devserve is; mpv and the hand-over are stubbed, so answering
either way only writes a line to the console."""
import os, sys, time, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import devserve
import nextup as n
from http.server import ThreadingHTTPServer

SANDBOX = os.path.join(tempfile.gettempdir(), "nextup_afk_serve")
devserve.isolate(n, SANDBOX)
n.load_saved_recs()

n.mpv_command = lambda *a: print("  mpv:", a, flush=True)
n.mpv_alive = lambda: True
n.raise_app_window = lambda: print("  raise window", flush=True)
n._hand_over = lambda current, follow_on: print(
    "  hand over:", current.get("title"), follow_on, flush=True)

n.ASK.update(active=True, since=time.time(), current={"type": "episode", "id": 1,
             "title": "My Hero Academia"}, follow_on=None, band="late",
             idle=52, title="My Hero Academia",
             next="My Hero Academia · S01E03 · Roaring Muscles")

PORT = 8772
print("afk serve on http://127.0.0.1:%d" % PORT, flush=True)
ThreadingHTTPServer(("127.0.0.1", PORT), n.Handler).serve_forever()
