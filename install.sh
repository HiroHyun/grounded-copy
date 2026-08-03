#!/bin/sh
# grounded-copy installer shim.
#
#   curl -fsSL https://raw.githubusercontent.com/HiroHyun/grounded-copy/main/install.sh | sh
#
# install.py holds every decision. This file resolves a Python 3 and hands the
# arguments over, so a clone and a pipe take the same code path and there is one
# implementation to keep correct.
set -eu

REPO_RAW="https://raw.githubusercontent.com/HiroHyun/grounded-copy/main"

# Probe once and keep the first interpreter that reports Python 3. Running
# `python install.py || python3 install.py` would run the installer twice.
py=""
for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 &&
       "$candidate" -c 'import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)' >/dev/null 2>&1; then
        py="$candidate"
        break
    fi
done

if [ -z "$py" ]; then
    echo "grounded-copy: Python 3 is required and resolved as neither python3 nor python" >&2
    exit 1
fi

# A clone runs its own copy. `$0` is a dash or a pipe under `curl | sh`, so the
# guard is the file's presence.
here=${0%/*}
[ "$here" = "$0" ] && here=.
if [ -f "$here/install.py" ]; then
    exec "$py" "$here/install.py" "$@"
fi

tmp=$(mktemp -d 2>/dev/null || mktemp -d -t grounded-copy)
trap 'rm -rf "$tmp"' EXIT INT TERM

if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$REPO_RAW/install.py" -o "$tmp/install.py"
elif command -v wget >/dev/null 2>&1; then
    wget -qO "$tmp/install.py" "$REPO_RAW/install.py"
else
    echo "grounded-copy: curl or wget is required to fetch install.py" >&2
    exit 1
fi

"$py" "$tmp/install.py" "$@"
