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

print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
