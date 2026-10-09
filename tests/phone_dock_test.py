"""The phone as a drive: in the docking station's list and the Drives view,
read and copied to over USB with adb.

No phone here. adb is a fake whose phone storage is a temp folder on this PC,
so every command the app sends is carried out for real against files — the
listing, the free space, the mkdir, the push, the rename. The library items
copied are small files made for the test, never the real films on E:."""
import sys, os, json, shlex, shutil, tempfile, time
sys.path.insert(0, r"X:\NextUp"); os.chdir(r"X:\NextUp"); sys.argv = ["nextup.py"]
import nextup as n
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from devserve import isolate
# isolate() switches the drive list and the copy off, so no test can ever
# write to a real drive. This one needs both — against the fake phone below
# only — so it keeps the real ones and switches off the USB drives instead.
real_list, real_worker = n.list_dock_drives, n.dock_copy_worker
isolate(n, os.path.join(tempfile.gettempdir(), "nextup_phonedock"))
n.list_dock_drives, n.dock_copy_worker = real_list, real_worker
n._list_local_dock_drives = lambda: []

results = []
def check(name, ok, detail=""):
    ok = bool(ok); results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- %s" % (detail,)) if detail != "" else ""))

WORK = os.path.join(here, "_work", "phonedock")
shutil.rmtree(WORK, ignore_errors=True)
PHONE_DISK = os.path.join(WORK, "phone")          # stands in for /storage/emulated/0
SRC = os.path.join(WORK, "library")
os.makedirs(PHONE_DISK); os.makedirs(SRC)
SERIAL = "R5CR11XSBFX"
DEST = "phone:" + SERIAL

def local(phone_path):
    """Where a phone path lives in the fake."""
    assert phone_path.startswith("/storage/emulated/0"), phone_path
    return os.path.join(PHONE_DISK, *phone_path[len("/storage/emulated/0"):].strip("/").split("/"))

calls = []
def fake_adb(*args, timeout=15):
    calls.append(args)
    a = list(args)
    if a[:1] == ["devices"]:
        return "List of devices attached\n%s\tdevice usb:1-1 model:SM_G998B\n" % SERIAL
    if a[:2] == ["-s", SERIAL]:
        a = a[2:]
    if a[:1] == ["push"]:
        dst = local(a[2])
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(a[1], dst)
        return "1 file pushed"
    if a[:1] != ["shell"]:
        return ""
    if len(a) == 2:                                   # one string, for the phone's own shell
        words = shlex.split(a[1], posix=True)
        if words[:2] == ["mkdir", "-p"]:
            os.makedirs(local(words[2]), exist_ok=True); return ""
        if words[:1] == ["mv"]:
            os.replace(local(words[1]), local(words[2])); return ""
        if words[:1] == ["stat"]:
            try: return "%d\n" % os.path.getsize(local(words[3]))
            except OSError: return ""
        if words[:2] == ["rm", "-f"]:
            try: os.remove(local(words[2]))
            except OSError: pass
            return ""
        if words[:1] == ["find"]:
            root = local(words[1]); out = []
            for dp, _d, fs in os.walk(root):
                for f in fs:
                    p = os.path.join(dp, f)
                    phone = "/storage/emulated/0/" + os.path.relpath(p, PHONE_DISK).replace(os.sep, "/")
                    out.append("%d %s" % (os.path.getsize(p), phone))
            return "\n".join(out) + "\n"
        return ""
    if a[1:3] == ["settings", "get"]:
        return "James's S21 Ultra\n"
    if a[1:2] == ["df"]:
        return "Filesystem 1K-blocks Used Available Use% Mounted on\n/dev/fuse 485000000 395000000 90177536 82% /storage/emulated\n"
    if a[1:3] == ["pm", "list"]:
        return "package:app.nextup.mobile\n"
    if a[1:2] == ["pidof"]:
        return ""                                     # app closed: no rescan to ask for
    return ""
n.usb_adb = fake_adb
n.usb_adb_path = lambda: r"C:\fake\adb.exe"

# --- the library: one film and one show, small files made here --------------------------
def make(name, size):
    p = os.path.join(SRC, name); open(p, "wb").write(os.urandom(size)); return p
film = make("Kingdom.of.Heaven.2005.DIRECTOR'S.CUT & more.mkv", 300000)
ep1, ep2 = make("Show.S01E01.mkv", 200000), make("Show.S01E02.mkv", 210000)
# Over the 50 MB line the Drives view uses to skip samples and trailers.
# Sparse, so it costs nothing on disk.
already = os.path.join(SRC, "Already.Here.2010.mkv")
with open(already, "wb") as fh:
    fh.truncate(51 * 1024 * 1024)
conn = n.db()
film_id = conn.execute("INSERT INTO movies (path,title,year,tmdb_id) VALUES (?,?,?,?)",
                       (film, "Kingdom of Heaven", 2005, "pd1")).lastrowid
have_id = conn.execute("INSERT INTO movies (path,title,year,tmdb_id) VALUES (?,?,?,?)",
                       (already, "Already Here", 2010, "pd2")).lastrowid
show_id = conn.execute("INSERT INTO shows (name,title,tmdb_id) VALUES (?,?,?)",
                       ("phonedock show", "Phonedock Show", "pd3")).lastrowid
for i, p in enumerate((ep1, ep2), 1):
    conn.execute("INSERT INTO episodes (path,show_id,season,episode) VALUES (?,?,?,?)",
                 (p, show_id, 1, i))
conn.commit(); conn.close()
n.LOCAL.loaded_at = 0; n.LIB.loaded_at = 0
# "Already Here" is on the phone already, in the user's own layout.
pre = local("/storage/emulated/0/Movies/Film & TV/Films/Already Here (2010)/Already.Here.2010.mkv")
os.makedirs(os.path.dirname(pre)); shutil.copyfile(already, pre)
selection = [{"kind": "movie", "id": film_id}, {"kind": "movie", "id": have_id},
             {"kind": "tvshow", "id": show_id}]

# --- in the lists ----------------------------------------------------------------------
drives = n.list_dock_drives()
phone = next((d for d in drives if d["letter"] == DEST), None)
check("the phone is in the drive list, by its own name, with its free space",
      phone and phone["label"] == "James's S21 Ultra" and phone["free"] > 80e9, phone)

# --- the Drives view --------------------------------------------------------------------
cat = n.drive_catalogue(DEST)
check("the Drives view reads what's on the phone", any(f.get("title") == "Already Here" or
      f.get("lib_id") == have_id for f in cat["films"]), [f.get("title") for f in cat["films"]])

# --- the price ----------------------------------------------------------------------------
import threading, urllib.request
from http.server import ThreadingHTTPServer
desk = ThreadingHTTPServer(("127.0.0.1", 8786), n.Handler)
threading.Thread(target=desk.serve_forever, daemon=True).start()
def post(path, body):
    req = urllib.request.Request("http://127.0.0.1:8786" + path, method="POST",
                                 data=json.dumps(body).encode())
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())
plan = post("/api/dock/plan", {"items": selection, "dest": DEST})
check("the plan prices only what isn't there yet, against the phone's free space",
      plan.get("count") == 3 and plan.get("already") == 1 and plan.get("free", 0) > 80e9
      and plan.get("fits"), plan)
sizes = plan.get("items") or {}
check("the plan sizes each ticked item, so the tray can show it",
      sizes.get("movie:%d" % film_id, {}).get("bytes") == 300000
      and sizes.get("tvshow:%d" % show_id, {}).get("bytes") == 410000
      and sizes.get("movie:%d" % have_id, {}).get("already") == 1
      and sizes.get("movie:%d" % have_id, {}).get("bytes") == 0, sizes)
check("the Drives view says the phone's free space", (cat.get("free") or 0) > 80e9, cat.get("free"))

# --- the copy -------------------------------------------------------------------------------
post("/api/dock/start", {"items": selection, "dest": DEST})
for _ in range(100):
    if not n.DOCK["running"]:
        break
    time.sleep(0.1)
root = "/storage/emulated/0/Movies/Film & TV"
got_film = local(root + "/Films/Kingdom of Heaven (2005)/" + os.path.basename(film))
got_ep = local(root + "/TV/Phonedock Show/Season 01/Show.S01E02.mkv")
check("the film lands in Film & TV/Films, whole — quotes and & in its name and all",
      os.path.isfile(got_film) and open(got_film, "rb").read() == open(film, "rb").read(),
      n.DOCK.get("errors"))
check("episodes land in Film & TV/TV, the phone's own folder name",
      os.path.isfile(got_ep) and os.path.getsize(got_ep) == os.path.getsize(ep2), n.DOCK.get("errors"))
leftover = [f for dp, _d, fs in os.walk(PHONE_DISK) for f in fs if f.endswith(".nextup-part")]
check("no half-copied file left looking finished", not leftover, leftover)
check("what was already there isn't copied again",
      not any(c[2:3] == ("push",) and c[3] == already for c in calls if len(c) > 3))
check("the job reports done, no errors", n.DOCK["step"] == "Done" and not n.DOCK["errors"]
      and n.DOCK["done"] == n.DOCK["total"] == 4, (n.DOCK["step"], n.DOCK["errors"], n.DOCK["done"]))

# --- cancelling before it starts copies nothing ---------------------------------------------------
shutil.rmtree(local(root + "/TV"))
n.DOCK_CANCEL.set()
n.dock_copy_worker(n.dock_plan_items(selection)[0], DEST)
check("cancel stops it", not os.path.exists(local(root + "/TV")), n.DOCK["step"])
desk.shutdown()

# --- one place to fill a drive: the library itself --------------------------------------
page = n.PAGE
check("SELECT is gone from the Library toolbar", 'id="libselect"' not in page)
check("the Settings docking station is gone", "<h3>Docking station</h3>" not in page
      and 'id="dock_drive"' not in page)
check("the Drives tab is gone", "['drives','Drives']" not in page and 'id="view-drives"' not in page)
lib_html = page[page.index('<div class="searchrow">'):page.index('<!-- ================= RATE')]
check("the library has the tick button, and the add bar under the filters",
      all(x in lib_html for x in ('id="libadd"', 'id="addbar"', 'id="drv_pick"', 'id="drv_browse"',
                                  'id="drv_refresh"', 'id="tray_list"', 'id="tray_status"',
                                  'id="tray_cancel"', 'id="tray_clear"')))
check("a floating green ADD with the selection's size beside it",
      'id="addfab"' in lib_html and 'id="addfab_size"' in lib_html and '>ADD</button>' in lib_html)
check("what's on a drive is still there to browse — in the library screen, not a panel",
      "function setDriveView(" in page and 'id="drv_notlib"' in lib_html
      and "function openDriveContents(" not in page)
check("ticking is the library's own tiles now", "#tiles-out .tile[data-key]" in page
      and "#drv_lib" not in page)

print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
