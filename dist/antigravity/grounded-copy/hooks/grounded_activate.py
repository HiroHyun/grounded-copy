#!/usr/bin/env python3
"""Antigravity SessionStart hook: inject the session policy as a system step."""

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
SWITCH_HINT = "grounded-profile (chat, copy, or off)"


def main(argv):
    _hook_io.utf8_streams()
    hook_dir = os.path.dirname(os.path.abspath(__file__))
    root = _hook_io.plugin_root(argv, hook_dir)

    if "--self-test" in argv:
        return _policy.self_test(root)

    _hook_io.drain_stdin()

    path = _hook_io.preference_arg(argv, PREFERENCE_PATH)
    profile, _source = _preference.resolve_preference(path)
    if profile not in _preference.ACTIVE:
        sys.stdout.write("{}\n")
        return 0

    skill = _policy.read_skill(root)
    if not skill:
        sys.stdout.write("{}\n")
        return 0

    policy = _policy.session_policy(skill, profile, SWITCH_HINT)
    sys.stdout.write(json.dumps({
        "injectSteps": [
            {"systemMessage": {"systemMessage": policy}},
        ],
    }) + "\n")
    return 0


if __name__ == "__main__":
    argv = sys.argv[1:]
    if "--self-test" in argv:
        sys.exit(main(argv))
    try:
        sys.exit(main(argv))
    except Exception:
        sys.stdout.write("{}\n")
        sys.exit(0)
