#!/bin/sh
# Resolve a Python 3 interpreter once, then run the named Antigravity hook.
hookdir=${0%/*}
[ "$hookdir" = "$0" ] && hookdir=.

case "$1" in
    grounded_activate.py) script=grounded_activate.py; fallback='{}' ;;
    grounded_tracker.py) script=grounded_tracker.py; fallback='{}' ;;
    grounded_gate.py) script=grounded_gate.py; fallback='{"decision":"allow"}' ;;
    *) printf '{}\n'; exit 0 ;;
esac
shift

for candidate in python python3; do
    if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)' >/dev/null 2>&1; then
        exec "$candidate" "$hookdir/$script" "$@"
    fi
done

printf '%s\n' "$fallback"
exit 0
