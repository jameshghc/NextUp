"""The version says the same thing everywhere: the app (APP_VERSION), the
phone build (android/pyproject.toml), the newest CHANGELOG.md heading and
the newest DEVELOPMENT_NOTES.md entry. A bump that only half happened, or a
day of changes with no changelog, shows up here rather than months later.
Reads files only."""
import os, re, sys

ROOT = r"X:\NextUp"
results = []
def check(name, ok, detail=""):
    ok = bool(ok); results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- %s" % (detail,)) if detail != "" else ""))

def read(name):
    return open(os.path.join(ROOT, name), encoding="utf-8").read()

app = re.search(r'^APP_VERSION = "([^"]+)"', read("nextup.py"), re.M).group(1)
phone = re.search(r'^version = "([^"]+)"', read(os.path.join("android", "pyproject.toml")), re.M).group(1)
log = re.search(r"^## (\d+\.\d+\.\d+)", read("CHANGELOG.md"), re.M)
notes = re.search(r"^## \d{4}-\d{2}-\d{2} — v(\d+\.\d+\.\d+)", read("DEVELOPMENT_NOTES.md"), re.M)

check("the phone build is the same version as the app", phone == app, (app, phone))
check("the newest changelog section is this version", log and log.group(1) == app, (app, log and log.group(1)))
check("the newest development notes are this version", notes and notes.group(1) == app, (app, notes and notes.group(1)))
section = read("CHANGELOG.md").split("## ", 2)[1] if log else ""
check("and it says what changed", section.count("\n- ") >= 1, section[:80])

print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
