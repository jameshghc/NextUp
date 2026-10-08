"""Build the Android app and put it on the phone.

    python android\build.py            copy, build, install
    python android\build.py --no-install

Copies nextup.py, its fonts and its logo in beside the app's own code
(with Unix line endings, like everything in this repo), then runs Briefcase
with the toolchain on X: — never C:, which is short of room — and installs
the APK over USB. The first build creates the Android project; later ones
update it in place, which is much quicker."""
import os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(HERE, "src")
BRIEFCASE = r"X:\DevTools\briefcase-venv\Scripts\briefcase.exe"
ADB = r"X:\DevTools\briefcase-data\tools\android_sdk\platform-tools\adb.exe"
ENV = dict(os.environ, BRIEFCASE_HOME=r"X:\DevTools\briefcase-data",
           GRADLE_USER_HOME=r"X:\DevTools\gradle")
APK = os.path.join(HERE, "build", "mobile", "android", "gradle", "app", "build",
                   "outputs", "apk", "debug", "app-debug.apk")


def copy_sources():
    with open(os.path.join(ROOT, "nextup.py"), "rb") as fh:
        code = fh.read().replace(b"\r\n", b"\n")
    with open(os.path.join(SRC, "nextup.py"), "wb") as fh:
        fh.write(code)
    shutil.copyfile(os.path.join(ROOT, "nextup_logo.png"), os.path.join(SRC, "nextup_logo.png"))
    shutil.rmtree(os.path.join(SRC, "nextup_fonts"), ignore_errors=True)
    shutil.copytree(os.path.join(ROOT, "nextup_fonts"), os.path.join(SRC, "nextup_fonts"))


def run(*args):
    print("\n>>> " + " ".join(args), flush=True)
    code = subprocess.run(list(args), cwd=HERE, env=ENV).returncode
    if code:
        sys.exit("failed (%d): %s" % (code, " ".join(args)))


def project_stale():
    """Briefcase writes the manifest — permissions included — only when it
    creates the Android project, and quick builds never revisit it. So a
    changed pyproject.toml means starting the project again, or a new
    permission silently never reaches the phone."""
    stamp = os.path.join(HERE, "build", "mobile", "android", ".pyproject-stamp")
    current = os.path.getmtime(os.path.join(HERE, "pyproject.toml"))
    try:
        with open(stamp) as fh:
            return float(fh.read()) != current, stamp, current
    except (OSError, ValueError):
        return True, stamp, current


def main():
    copy_sources()
    stale, stamp, current = project_stale()
    if stale:
        shutil.rmtree(os.path.join(HERE, "build", "mobile", "android"), ignore_errors=True)
    if not os.path.isdir(os.path.join(HERE, "build", "mobile", "android")):
        run(BRIEFCASE, "create", "android", "--no-input")
        run(BRIEFCASE, "build", "android", "--no-input")
        with open(stamp, "w") as fh:
            fh.write(repr(current))
    else:
        run(BRIEFCASE, "build", "android", "--update", "--update-resources", "--no-input")
    if "--no-install" not in sys.argv:
        run(ADB, "install", "-r", APK)
    print("\nbuilt: " + APK)


if __name__ == "__main__":
    main()
