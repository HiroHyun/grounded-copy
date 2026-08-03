#!/bin/sh
# Resolve a Python 3 interpreter once, then run the named hook script once.
#
# `python X.py || python3 X.py` re-runs the script whenever the first
# interpreter exits nonzero for any reason, which on SessionStart emits the
# session policy twice. Probing first and running once avoids that.
#
# The first argument is matched against a closed set and a literal is assigned
# on match, so the executed command line derives from this file. An unknown
# name exits 0 with no output.
#
# `exec` hands the interpreter's exit code back to the caller, which the
# `--set` path needs: 0 recorded, 1 persistence failure, 2 rejected value.
#
# Exit 0 when no interpreter resolves: a style hook stays non-blocking.
#
# Usage: sh run.sh grounded_activate.py|grounded_tracker.py [args...]

# Parameter expansion, no external `dirname`: this script has to survive a
# degraded PATH, which is one of the cases it exists to handle.
hookdir=${0%/*}
[ "$hookdir" = "$0" ] && hookdir=.

case "$1" in
    grounded_activate.py) script=grounded_activate.py ;;
    grounded_tracker.py) script=grounded_tracker.py ;;
    *) exit 0 ;;
esac
shift

for candidate in python python3; do
    if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)' >/dev/null 2>&1; then
        exec "$candidate" "$hookdir/$script" "$@"
    fi
done

exit 0
