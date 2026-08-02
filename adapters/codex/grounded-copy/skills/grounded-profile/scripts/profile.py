#!/usr/bin/env python3
"""Explicit Codex profile controller."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS = os.path.join(os.path.dirname(ROOT), "..", "hooks")
sys.path.insert(0, os.path.abspath(HOOKS))
import _hook_io  # noqa: E402
import _policy  # noqa: E402
import _preference  # noqa: E402

OPS = {"chat": "chat", "copy": "copy", "off": "off", "status": "status"}
EXIT_PERSISTENCE = 1
EXIT_REJECTED = 2
PREFERENCE_PATH = os.path.join(
    os.environ.get("CODEX_HOME") or os.path.join(os.path.expanduser("~"), ".codex"),
    "grounded-copy",
    "profile",
)

def main(argv):
    raw = argv[0].strip().lower() if argv else "status"
    operation = OPS.get(raw)
    if operation is None or len(argv) != 1:
        print("grounded: choose exactly chat, copy, off, or status")
        return EXIT_REJECTED
    if operation == "status":
        print(_preference.status_line(PREFERENCE_PATH))
        return 0
    ok, detail = _preference.write_preference(operation, PREFERENCE_PATH)
    if not ok:
        print(detail)
        return EXIT_PERSISTENCE
    print(_preference.status_line(PREFERENCE_PATH))
    print()
    root = os.environ.get("PLUGIN_ROOT") or os.path.abspath(os.path.join(ROOT, "..", ".."))
    skill = _policy.read_skill(root, "skills/grounded-copy/SKILL.md")
    source = "recorded at " + _preference.preference_path(PREFERENCE_PATH)
    print(_policy.governing_directive(skill, operation, source))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
