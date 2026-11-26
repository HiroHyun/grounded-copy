#!/usr/bin/env python3
"""Antigravity PreInvocation hook, and the profile control CLI.

PreInvocation fires before every model call in a turn; emitting only on
invocationNum == 0 injects the turn reminder once per user prompt so it does
not pile up across tool-call steps.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _hook_io  # noqa: E402
import _policy  # noqa: E402
import _preference  # noqa: E402

PREFERENCE_PATH = os.path.join(
    os.environ.get("ANTIGRAVITY_CONFIG_DIR") or os.path.join(
        os.path.expanduser("~"), ".gemini", "config"
    ),
    "grounded-copy",
    "profile",
)
RESTORE_HINT = "grounded-profile (chat)"

EXIT_OK = 0
EXIT_PERSISTENCE = 1
EXIT_REJECTED = 2
CONTROL_FLAGS = ("--set", "--status")


def set_mode(argv, hook_dir):
    index = argv.index("--set")
    raw = argv[index + 1] if index + 1 < len(argv) else ""
    path = _hook_io.preference_arg(argv, PREFERENCE_PATH)
    if not raw.strip():
        print(_preference.status_line(path, RESTORE_HINT))
        return EXIT_OK

    profile = _preference.canonical_argument(raw)
    if profile is None:
        print(
            "grounded: unknown profile %r; choose chat, copy, or off"
            % raw.strip().lower()
        )
        return EXIT_REJECTED

    ok, detail = _preference.write_preference(profile, path)
    if not ok:
        print(detail)
        return EXIT_PERSISTENCE

    print(_preference.status_line(path, RESTORE_HINT))
    print()
    skill = _policy.read_skill(_hook_io.plugin_root(argv, hook_dir))
    source = "recorded at " + _preference.preference_path(path)
    print(_policy.governing_directive(skill, profile, source))
    return EXIT_OK


def main(argv):
    _hook_io.utf8_streams()
    hook_dir = os.path.dirname(os.path.abspath(__file__))

    if "--set" in argv:
        return set_mode(argv, hook_dir)
    if "--status" in argv:
        path = _hook_io.preference_arg(argv, PREFERENCE_PATH)
        print(_preference.status_line(path, RESTORE_HINT))
        return EXIT_OK

    event = _hook_io.read_event() or {}
    if event.get("invocationNum", 0) != 0:
        sys.stdout.write("{}\n")
        return EXIT_OK

    profile, _source = _preference.resolve_preference(
        _hook_io.preference_arg(argv, PREFERENCE_PATH)
    )
    if profile not in _preference.ACTIVE:
        sys.stdout.write("{}\n")
        return EXIT_OK

    sys.stdout.write(json.dumps({
        "injectSteps": [
            {"systemMessage": {"systemMessage": _policy.turn_reminder(profile)}},
        ],
    }) + "\n")
    return EXIT_OK


if __name__ == "__main__":
    argv = sys.argv[1:]
    if any(flag in argv for flag in CONTROL_FLAGS):
        sys.exit(main(argv))
    try:
        sys.exit(main(argv))
    except Exception:
        sys.stdout.write("{}\n")
        sys.exit(0)
