"""One test 'computer': runs nextup.py from its own stage folder, headless,
with a fast sync loop and a /test/* hook to simulate playback endings."""
import os, sys, json, threading

stage, port = sys.argv[1], int(sys.argv[2])
sys.path.insert(0, stage)
os.chdir(stage)
sys.argv = ["nextup.py"]
import nextup
from http.server import ThreadingHTTPServer

assert os.path.dirname(os.path.abspath(nextup.DB_PATH)) == os.path.abspath(stage)
nextup.SYNC_POLL_SECONDS = 3

orig_post = nextup.Handler.do_POST


def do_POST(self):
    if self.path.startswith("/test/"):
        data = self.read_body()
        kind, item_id = data["kind"], int(data["id"])
        table = "movies" if kind == "movie" else "episodes"
        if self.path == "/test/stop":
            nextup._record_position(table, kind, item_id, float(data["position"]),
                                    float(data["total"]), ran_for=600)
        elif self.path == "/test/watched":
            nextup._record_play(table, kind, item_id, seconds=1500,
                                position=data.get("total"), total=data.get("total"))
        elif self.path == "/test/played":
            nextup.log_event(kind, item_id, nextup.LOCAL.field(kind, item_id, "title"), "played")
        return self.send_json({"ok": True})
    return orig_post(self)


nextup.Handler.do_POST = do_POST
threading.Thread(target=nextup.sync_loop, daemon=True).start()
print("runner %s on %d" % (stage, port), flush=True)
ThreadingHTTPServer(("127.0.0.1", port), nextup.Handler).serve_forever()
