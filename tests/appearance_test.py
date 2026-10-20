"""The look: Classic or Glass, and the four things you can set in Settings ->
Appearance (accent, glass strength, background art, corner roundness).
Every value is checked and clamped on the server, so nothing saved can
break the page. Against a sandbox copy (devserve.isolate)."""
import sys, os, re, json, tempfile, threading, urllib.request
sys.path.insert(0, r"X:\NextUp"); os.chdir(r"X:\NextUp"); sys.argv = ["nextup.py"]
import nextup as n
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from devserve import isolate
isolate(n, os.path.join(tempfile.gettempdir(), "nextup_appearance"))

results = []
def check(name, ok, detail=""):
    ok = bool(ok); results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- %s" % (detail,)) if detail != "" else ""))

# --- the settings, checked -----------------------------------------------------------
n.CONFIG.pop("appearance", None)
d = n.appearance_settings()
check("defaults on the PC: Glass, marigold, middling strength",
      d["theme"] == "glass" and d["accent"] == "marigold" and 0 <= d["glass"] <= 100
      and 0 <= d["art"] <= 100 and d["round"] is None, d)
n.PLATFORM = "android"
check("on the phone, Classic unless chosen (blur costs battery)", n.appearance_settings()["theme"] == "classic")
n.PLATFORM = "windows"
n.CONFIG["appearance"] = {"theme": "evil", "accent": "#ff0000", "glass": 500, "art": "abc", "round": -40}
d = n.appearance_settings()
check("nonsense is clamped or ignored, never kept",
      d["theme"] == "glass" and d["accent"] == "marigold" and d["glass"] == 100
      and d["art"] == n.APPEARANCE_DEFAULTS["art"] and d["round"] == 0, d)
n.CONFIG["appearance"] = "not even a dict"
check("a damaged setting reads as the defaults", n.appearance_settings()["accent"] == "marigold")

# --- what the page is given ---------------------------------------------------------------
def look(**kw):
    n.CONFIG["appearance"] = kw
    return n.appearance_look()
a = look(theme="glass", accent="teal", glass=0)
b = look(theme="glass", accent="teal", glass=100)
check("the accent is one of the presets, everywhere it's used",
      a["vars"]["--marigold"] == n.ACCENTS["teal"] and re.fullmatch(r"\d+,\d+,\d+", a["vars"]["--accent-rgb"]), a["vars"])
blur = lambda l: int(l["vars"]["--glass-blur"].rstrip("px"))
alpha = lambda l: float(l["vars"]["--glass-panel"].rsplit(",", 1)[1].rstrip(")"))
check("more glass: more blur, more see-through", blur(b) > blur(a) and alpha(b) < alpha(a), (blur(a), blur(b), alpha(a), alpha(b)))
check("Glass gives the body its class", "glass" in a["classes"])
c = look(theme="classic", round=None)
check("Classic keeps today's corners unless you move the slider", "glass" not in c["classes"]
      and "customround" not in c["classes"])
r = look(theme="classic", round=100)
check("moving the corner slider applies it", "customround" in r["classes"] and r["vars"]["--r-user"] == "22px", r["vars"].get("--r-user"))
off = look(theme="glass", art=0)
check("art at 0 hides it", off["vars"]["--art-opacity"] == "0", off["vars"]["--art-opacity"])

# --- served before the page draws: no flash of the old look ---------------------------------
n.CONFIG["appearance"] = {"theme": "glass", "accent": "rose"}
html = n.page_html()
body = re.search(r"<body[^>]*>", html).group(0)
check("the page arrives already dressed", 'class="glass"' in body and "--marigold:" + n.ACCENTS["rose"] in body, body[:200])
n.PLATFORM = "android"
n.CONFIG["appearance"] = {"theme": "classic"}
body = re.search(r"<body[^>]*>", n.page_html()).group(0)
check("and the phone still gets its own class", "android" in body, body[:120])
n.PLATFORM = "windows"

# --- the route -----------------------------------------------------------------------------
desk = n.ThreadingHTTPServer(("127.0.0.1", 8793), n.Handler)
threading.Thread(target=desk.serve_forever, daemon=True).start()
def post(path, body):
    req = urllib.request.Request("http://127.0.0.1:8793" + path, data=json.dumps(body).encode(),
                                 method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())
got = post("/api/appearance", {"theme": "glass", "accent": "violet", "glass": 70, "art": 40, "round": 60})
check("saving returns the checked settings and the look", got["settings"]["accent"] == "violet"
      and got["look"]["vars"]["--marigold"] == n.ACCENTS["violet"], got.get("settings"))
check("and keeps them", json.load(open(n.CONFIG_PATH, encoding="utf-8"))["appearance"]["accent"] == "violet")
with urllib.request.urlopen("http://127.0.0.1:8793/api/appearance", timeout=10) as r:
    shown = json.loads(r.read())
check("Settings can read the choices without changing them", shown["settings"]["accent"] == "violet"
      and len(shown["accents"]) == len(n.ACCENTS), shown.get("settings"))
got = post("/api/appearance", {"reset": True})
check("reset goes back to the defaults", got["settings"] == n.appearance_settings()
      and got["settings"]["accent"] == "marigold", got["settings"])
desk.shutdown()

# --- the page ------------------------------------------------------------------------------
page = n.PAGE
check("no marigold left hard-coded: the accent reaches everything",
      "rgba(224,163,62" not in page and "#e0a33e" not in page.split(":root{", 1)[1].split("}", 1)[1])
check("an Appearance tab with the four controls and a reset",
      'data-tab="appearance"' in page and all(('id="ap_%s"' % k) in page for k in ("accent", "glass", "art", "round"))
      and 'id="ap_reset"' in page and "['appearance', 'Appearance']" in page)
check("the Glass layer and the art behind it", "body.glass " in page and 'id="roomart"' in page
      and "function setRoomArt(" in page)
check("the pick's art goes behind the page", "setRoomArt(" in page[page.find("function showPick("):][:3000])

# 2026-10-19, the user's notes on Glass: a white sheen over the Now page
# (the panels were a light grey, 102,102,113 at .38), and the tag chooser
# boxed in so its chips touched the box's edge.
n.CONFIG["appearance"] = {}
mid = n.appearance_look()["vars"]["--glass-panel"]
rgb = [int(x) for x in mid[mid.index("(") + 1:].split(",")[:3]]
check("the glass is a dark tint, not a light grey: the frost is the blur", max(rgb) <= 60, mid)
_glass = page[page.find("body.glass :is("):][:1200]
_rule = _glass[:_glass.find("}")]
check("and no white sheen laid over the panels in Glass", "background-image:none" in _rule, _rule[-200:])
check("the tag chooser floats: no box behind it", ".nowchooser" not in _rule.split("{")[0])
check("the tags start level with the Continue cards, not their heading",
      "#view-now:has(#unfinished-sec:not(.hidden)) > #nowside{" in page)

# 2026-10-19, second round: darker above all (bright shows like The
# Simpsons still lit the page), the mock-up's black header with gold
# lettering, BACK beside NEXT, and buttons that don't fade into the glass.
n.CONFIG["appearance"] = {}
mid = n.appearance_look()["vars"]["--glass-panel"]
check("the panels are mostly solid at the default strength", float(mid.rsplit(",", 1)[1].rstrip(")")) >= 0.5, mid)
full = n.appearance_look(dict(n.appearance_settings(), glass=100))["vars"]["--glass-panel"]
check("and never thinner than .4 even at full frost", float(full.rsplit(",", 1)[1].rstrip(")")) >= 0.4, full)
_art = page[page.find("#roomart{"):][:400]
_b = re.search(r"brightness\(([\d.]+)\)", _art)
check("the art behind the page is dimmed hard", _b and float(_b.group(1)) <= 0.4, _art[:200])
check("and the film's own backdrop in the pick card fades further in Glass", "body.glass .hero{" in page)
check("the black header with gold lettering", "body.glass #titlebar{" in page
      and "background:#000" in page[page.find("body.glass #titlebar{"):][:200])
check("BACK beside NEXT on the pick", "'iconbtn pickback'" in page
      and "pickback" in page[page.find("function paintBack("):][:400])
check("buttons on glass have a fill and a firm outline", "body.glass :is(.iconbtn,.watchtoggle,.favtoggle){" in page)
# 2026-10-20: the pick's art is the Now page's alone. The Library (and the
# rest) stay a neutral grey glass, not tinted by whatever Now last showed.
check("the art behind the page shows on Now only", "body:not(.onnow) #roomart{" in page
      and "document.body.classList.toggle('onnow', view === 'now')" in page)

js = "\n;\n".join(re.findall(r"<script>(.*?)</script>", page, re.S))
open(os.path.join(tempfile.gettempdir(), "nextup_appearance", "page.js"), "w", encoding="utf-8").write(js)
import subprocess
rr = subprocess.run(["node", "-e", "new Function(require('fs').readFileSync(process.argv[1],'utf8'));console.log('ok')",
                     os.path.join(tempfile.gettempdir(), "nextup_appearance", "page.js")], capture_output=True, text=True)
check("page script parses", rr.stdout.strip() == "ok", rr.stderr[:300])

print("\n%d/%d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
