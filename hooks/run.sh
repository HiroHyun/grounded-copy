#!/bin/sh
# Resolve a Python 3 interpreter once, then run the named hook script once.
#
# `python X.py || python3 X.py` re-runs the script whenever the first
# interpreter exits nonzero for any reason, which on SessionStart emits the
# ruleset twice. Probing first, running once, avoids that.
#
# Exit 0 when no interpreter resolves: a style hook never breaks a session.
#
# Usage: sh run.sh <script-name> [args...]

# Parameter expansion, no external `dirname`: this script has to survive a
# degraded PATH, which is one of the cases it exists to handle.
hookdir=${0%/*}
[ "$hookdir" = "$0" ] && hookdir=.
script="$1"
[ -n "$script" ] || exit 0
shift

for candidate in python python3; do
    if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)' >/dev/null 2>&1; then
        exec "$candidate" "$hookdir/$script" "$@"
    fi
done

exit 0
