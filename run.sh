#!/bin/sh
# Next Up on a Mac or Linux machine. Run this from inside the Next Up folder.
#
# On a Mac this folder normally ships its own Python and mpv under mac/, so
# there is nothing to install — see "Next Up.command", which is the same
# thing you can double-click. This script is the terminal equivalent, and
# the fallback path for Linux.
cd "$(dirname "$0")" || exit 1

if [ -x "./mac/python3/bin/python3" ]; then
    exec "./mac/python3/bin/python3" nextup.py
fi

# No bundled runtime: use the system python3 and make sure pywebview is
# there. A venv rather than "pip install --user", which modern Python
# refuses outright on a managed install (PEP 668).
if [ ! -x "./.venv/bin/python3" ]; then
    echo "Setting up a local environment in .venv ..."
    python3 -m venv .venv || exit 1
    ./.venv/bin/python3 -m pip install --quiet --upgrade pip
    ./.venv/bin/python3 -m pip install --quiet -r requirements.txt || exit 1
fi
exec ./.venv/bin/python3 nextup.py
