"""The phone link, PC side: pairing, the gate, the snapshot, downloads,
sync and being found. Against a sandbox copy of everything (see
devserve.isolate), on ports 8798/8799 so it can run beside the real app,
and with no network beyond this machine."""
import sys, os, re, json, time, tempfile
sys.path.insert(0, r"X:\NextUp"); os.chdir(r"X:\NextUp"); sys.argv = ["nextup.py"]
import nextup as n
here = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(here, "_work")
os.makedirs(WORK, exist_ok=True)
sys.path.insert(0, here)
from devserve import isolate
isolate(n, os.path.join(tempfile.gettempdir(), "nextup_phonelink"))

results = []
def check(name, ok, detail=""):
    ok = bool(ok); results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- %s" % (detail,)) if detail != "" else ""))

def raises(fn, *a):
    try:
        fn(*a)
    except n.AppError as exc:
        return str(exc) or True
    return False

PHONE = "abcdef0123456789"

# --- Task 1: pairing and tokens ------------------------------------------------
code = n.phone_pair_start()["code"]
check("code is four digits", re.fullmatch(r"\d{4}", code), code)
token = n.phone_pair_finish(code, PHONE, "S24 Ultra")
dev = n.phone_device_for_token(token)
check("right code gives a token, stored only as a hash",
      len(token) >= 40 and token not in json.dumps(n.CONFIG) and dev and dev["id"] == PHONE,
      dev)
check("code is single use", raises(n.phone_pair_finish, code, PHONE, "S24 Ultra"))
code = n.phone_pair_start()["code"]
n.PHONE_PAIRING["expires"] = time.time() - 1
check("expired code refused", raises(n.phone_pair_finish, code, PHONE, "S24 Ultra"))
code = n.phone_pair_start()["code"]
wrong = "%04d" % ((int(code) + 1) % 10000)
for _ in range(5):
    raises(n.phone_pair_finish, wrong, PHONE, "S24 Ultra")
check("code dies after five wrong tries", raises(n.phone_pair_finish, code, PHONE, "S24 Ultra"))
code = n.phone_pair_start()["code"]
check("bad device id refused", raises(n.phone_pair_finish, code, "../x", "S24 Ultra"))
n.phone_forget(PHONE)
check("forget revokes", n.phone_device_for_token(token) is None)

# --- Task 2: the listener and its gate -------------------------------------------
import urllib.request, urllib.error
PORT = 8799
BASE = "http://127.0.0.1:%d" % PORT

def call(method, path, token=None, body=None, headers=None, raw=None):
    """(status, headers, bytes), errors returned rather than raised."""
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(BASE + path, data=data, method=method)
    if token:
        req.add_header("Authorization", "Bearer " + token)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.headers, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()

n.phone_link_start(PORT, "127.0.0.1")
code = n.phone_pair_start()["code"]
st, _h, body = call("POST", "/phone/pair", body={"code": code, "device_id": PHONE, "name": "S24 Ultra"})
token = json.loads(body).get("token") if st == 200 else None
check("pairing over the wire", st == 200 and token, (st, body[:120]))
st0 = call("GET", "/phone/hello")[0]
st1, _h, body = call("GET", "/phone/hello", token)
check("hello needs the token", st0 == 401 and st1 == 200
      and json.loads(body).get("version") == n.APP_VERSION, (st0, st1, body[:120]))
desk = [call("GET", p, token)[0] for p in ("/", "/api/status", "/api/library/status")] + \
       [call("POST", p, token, body={})[0] for p in ("/api/sorter/aside", "/api/play")]
check("desktop routes don't exist here, token or not", desk == [404] * 5, desk)
code = n.phone_pair_start()["code"]
wrong = "%04d" % ((int(code) + 1) % 10000)
st = call("POST", "/phone/pair", body={"code": wrong, "device_id": PHONE, "name": "S24"})[0]
check("wrong code over the wire is 403", st == 403, st)
n.phone_link_stop()
try:
    call("GET", "/phone/hello", token); closed = False
except urllib.error.URLError as exc:
    closed = isinstance(exc.reason, ConnectionRefusedError) or "refused" in str(exc).lower()
check("stop closes the port", closed)
n.phone_link_start(PORT, "127.0.0.1")      # back up for what follows

print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
