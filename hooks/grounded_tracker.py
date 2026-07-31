#!/usr/bin/env python3
"""UserPromptSubmit hook, and the profile control CLI.

Two roles with a boundary between them:

- As a hook it is **read-only**. It resolves the preference and emits the turn
  reminder, which holds against the per-turn injections other plugins make.
- As `--set` it is the mutation path. _preference.write_preference() is the
  sole writer and this is its only caller. It prints the status line and the
  governing directive for the new profile, so the switch reaches the transcript
  in the same turn the user typed the command.

An earlier build also parsed whole-prompt control instructions here.
references/setup.md records the removal and the evidence behind it.

Usage:
    grounded_tracker.py [--plugin-root DIR]
    grounded_tracker.py --set chat|copy|off
    grounded_tracker.py --status

Exit codes for `--set`: 0 recorded, 1 persistence failure, 2 rejected value.
An empty value reports status and exits 0, since it requests no change.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _hook_io  # noqa: E402
import _policy  # noqa: E402
import _preference  # noqa: E402

EXIT_OK = 0
EXIT_PERSISTENCE = 1
EXIT_REJECTED = 2

CONTROL_FLAGS = ("--set", "--status")


def set_mode(argv, hook_dir):
    """`--set PROFILE`: record the preference, print the governing directive."""
    index = argv.index("--set")
    raw = argv[index + 1] if index + 1 < len(argv) else ""
    if not raw.strip():
        print(_preference.status_line())
        return EXIT_OK

    profile = _preference.canonical_argument(raw)
    if profile is None:
        print(
            "grounded: unknown profile %r; choose chat, copy, or off"
            % raw.strip().lower()
        )
        return EXIT_REJECTED

    ok, detail = _preference.write_preference(profile)
    if not ok:
        print(detail)
        return EXIT_PERSISTENCE

    print(_preference.status_line())
    print()
    skill = _policy.read_skill(_hook_io.plugin_root(argv, hook_dir))
    source = "recorded at " + _preference.preference_path()
    print(_policy.governing_directive(skill, profile, source))
    return EXIT_OK


def main(argv):
    hook_dir = os.path.dirname(os.path.abspath(__file__))

    if "--status" in argv:
        print(_preference.status_line())
        return EXIT_OK
    if "--set" in argv:
        return set_mode(argv, hook_dir)

    _hook_io.drain_stdin()

    profile, _source = _preference.resolve_preference()
    if profile not in _preference.ACTIVE:
        return EXIT_OK

    sys.stdout.write(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": _policy.turn_reminder(profile),
        }
    }))
    return EXIT_OK


if __name__ == "__main__":
    argv = sys.argv[1:]
    if any(flag in argv for flag in CONTROL_FLAGS):
        # An explicit request reports its own outcome, failures included.
        sys.exit(main(argv))
    try:
        # A hook stays non-blocking: a style reminder that breaks a session
        # start costs more than the reminder is worth.
        sys.exit(main(argv))
    except Exception:
        sys.exit(0)
