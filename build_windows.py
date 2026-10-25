"""Build the Windows app: one NextUp-<version>-windows.exe in dist/.

    python build_windows.py                  build what's committed (HEAD)
    python build_windows.py --ref v0.2.0     build a tag or any other commit
    python build_windows.py --working-tree   build the files as they are now
    python build_windows.py --venv PATH      use (or make) the build venv there

Builds from a commit by default, not from the folder: a release should be
exactly something in the history, and the working copy is often mid-change.

What goes in, and only this: nextup.py, nextup.ico, nextup_logo.png and the
nextup_fonts folder. They're taken out of git (or copied by name from the
working tree) into build/windows/stage, so nothing else in the folder - the
config with its keys, the library, the art, the resume points - can reach
PyInstaller even by accident. The bundle is listed and checked afterwards,
and the build fails if anything private turns up in it.

PyInstaller runs from its own venv (build/pyinstaller-venv unless --venv
says otherwise), made on the first build, so nothing lands in the global
Python. Everything under build/ and dist/ is gitignored.

One packaging quirk worth knowing: a frozen nextup.py looks for its fonts,
logo and icon BESIDE the exe, not inside it (HERE is the exe's folder). So
the exe carries them inside, and a small runtime hook copies any that are
missing out beside it on start-up. A lone exe in a fresh folder therefore
looks right from its first launch, at the cost of a nextup_fonts folder and
two images appearing next to it.
"""
import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import tarfile

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build", "windows")
STAGE = os.path.join(BUILD, "stage")
DIST = os.path.join(ROOT, "dist")
ASSETS = ["nextup.py", "nextup.ico", "nextup_logo.png", "nextup_fonts"]

# Anything with one of these in its name must never be in the bundle.
PRIVATE = re.compile(r"nextup_(config|library|cache|dismissed|recs|youtube|playing|errors)"
                     r"|nextup_(art|resume|phone_sync)[\\/]|\.db$|\.db-|tmdb.?key|secret",
                     re.I)

RUNTIME_HOOK = r'''
# Next Up runtime hook: put the fonts, logo and icon beside the exe if they
# aren't there yet. A frozen nextup.py serves them from the exe's folder.
import os, shutil, sys
def _nextup_unpack():
    src = os.path.join(getattr(sys, "_MEIPASS", ""), "nextup_assets")
    dest = os.path.dirname(os.path.abspath(sys.executable))
    if not os.path.isdir(src):
        return
    for name in os.listdir(src):
        target = os.path.join(dest, name)
        path = os.path.join(src, name)
        try:
            if os.path.isdir(path):
                # Into a folder that's already there, too: a newer exe brings
                # new files (fonts added in 0.2.2), and its .css lists them.
                os.makedirs(target, exist_ok=True)
                for inner in os.listdir(path):
                    there = os.path.join(target, inner)
                    if inner.endswith(".css") or not os.path.exists(there):
                        shutil.copyfile(os.path.join(path, inner), there)
            elif not os.path.exists(target):
                shutil.copyfile(path, target)
        except OSError:
            pass        # a read-only folder: the app still runs, just plainer
_nextup_unpack()
'''


def run(args, **kw):
    print(">>> " + " ".join(args), flush=True)
    subprocess.run(args, check=True, **kw)


def stage(ref, working_tree):
    shutil.rmtree(STAGE, ignore_errors=True)
    os.makedirs(STAGE)
    if working_tree:
        for name in ASSETS:
            src = os.path.join(ROOT, name)
            if os.path.isdir(src):
                shutil.copytree(src, os.path.join(STAGE, name))
            else:
                shutil.copyfile(src, os.path.join(STAGE, name))
        return "working tree"
    commit = subprocess.run(["git", "rev-parse", "--short", ref + "^{commit}"], cwd=ROOT,
                            capture_output=True, text=True, check=True).stdout.strip()
    data = subprocess.run(["git", "archive", "--format=tar", commit] + ASSETS, cwd=ROOT,
                          capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        tar.extractall(STAGE, filter="data")
    return commit


def app_version():
    with open(os.path.join(STAGE, "nextup.py"), encoding="utf-8") as fh:
        m = re.search(r'^APP_VERSION = "([^"]+)"', fh.read(), re.M)
    if not m:
        sys.exit("couldn't find APP_VERSION in nextup.py")
    return m.group(1)


def venv_python(venv):
    py = os.path.join(venv, "Scripts", "python.exe")
    if not os.path.isfile(py):
        run([sys.executable, "-m", "venv", venv])
    try:
        subprocess.run([py, "-c", "import PyInstaller, webview"], check=True,
                       capture_output=True)
    except subprocess.CalledProcessError:
        run([py, "-m", "pip", "install", "--quiet", "pyinstaller", "pywebview"])
    return py


def bundle_contents(py, exe):
    """Every file inside the one-file exe, by name."""
    code = ("import sys\n"
            "from PyInstaller.archive.readers import CArchiveReader\n"
            "for name in CArchiveReader(sys.argv[1]).toc: print(name)\n")
    out = subprocess.run([py, "-c", code, exe], capture_output=True, text=True, check=True)
    return out.stdout.split()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ref", default="HEAD")
    ap.add_argument("--working-tree", action="store_true")
    ap.add_argument("--venv", default=os.path.join(ROOT, "build", "pyinstaller-venv"))
    opts = ap.parse_args()

    source = stage(opts.ref, opts.working_tree)
    version = app_version()
    name = "NextUp-%s-windows" % version
    print("Building %s from %s" % (name, source))

    hook = os.path.join(BUILD, "nextup_unpack_assets.py")
    with open(hook, "w", encoding="utf-8") as fh:
        fh.write(RUNTIME_HOOK)

    py = venv_python(opts.venv)
    sep = os.pathsep
    run([py, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--noconsole",
         "--name", name,
         "--icon", os.path.join(STAGE, "nextup.ico"),
         "--add-data", os.path.join(STAGE, "nextup_fonts") + sep + "nextup_assets/nextup_fonts",
         "--add-data", os.path.join(STAGE, "nextup_logo.png") + sep + "nextup_assets",
         "--add-data", os.path.join(STAGE, "nextup.ico") + sep + "nextup_assets",
         "--runtime-hook", hook,
         "--exclude-module", "tkinter",
         "--distpath", DIST,
         "--workpath", os.path.join(BUILD, "work"),
         "--specpath", BUILD,
         os.path.join(STAGE, "nextup.py")])

    exe = os.path.join(DIST, name + ".exe")
    contents = bundle_contents(py, exe)
    private = [n for n in contents if PRIVATE.search(n)]
    if private:
        os.remove(exe)
        sys.exit("STOPPED: private-looking files in the bundle, exe deleted:\n  "
                 + "\n  ".join(private))
    ours = [n for n in contents if n.startswith("nextup") or n == "nextup"]
    print("\nApp files in the bundle:")
    for n in ours:
        print("  " + n)
    print("\n%d entries checked, none private." % len(contents))
    print("built: %s (%.1f MB, from %s)" % (exe, os.path.getsize(exe) / 1e6, source))


if __name__ == "__main__":
    main()
