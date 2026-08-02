#!/usr/bin/env python3
"""SessionStart hook: put the session policy in context.

Stdout becomes session context, so the rules arrive with no skill-trigger
judgment involved. Registered with no matcher, so it also fires after every
compaction.

_policy.py assembles the text from SKILL.md at runtime, which lets a rule edit
land with no code change. This hook is read-only: it resolves the preference
and writes nothing.

Usage:
    grounded_activate.py [--plugin-root DIR]
    grounded_activate.py --self-test [--plugin-root DIR]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _hook_io  # noqa: E402
import _policy  # noqa: E402
import _preference  # noqa: E402

# Adapter seam: a copied entrypoint may set these paths for its host.
PREFERENCE_PATH = os.path.join(
    os.environ.get("CODEX_HOME") or os.path.join(
        os.path.expanduser("~"), ".codex"
    ),
    "grounded-copy",
    "profile",
)
SKILL_PATH = "skills/grounded-copy/SKILL.md"


def _preference_path(argv):
    if "--preference-path" in argv:
        index = argv.index("--preference-path")
        if index + 1 < len(argv):
            return argv[index + 1]
    return PREFERENCE_PATH


def main(argv):
    hook_dir = os.path.dirname(os.path.abspath(__file__))
    root = _hook_io.plugin_root(argv, hook_dir)

    if "--self-test" in argv:
        return _policy.self_test(root, SKILL_PATH)

    _hook_io.drain_stdin()

    path = _preference_path(argv)
    profile, _source = _preference.resolve_preference(path)
    if profile not in _preference.ACTIVE:
        return 0

    skill = _policy.read_skill(root, SKILL_PATH)
    if not skill:
        return 0

    sys.stdout.write(_policy.session_policy(skill, profile))
    return 0


if __name__ == "__main__":
    argv = sys.argv[1:]
    if "--self-test" in argv:
        sys.exit(main(argv))
    try:
        sys.exit(main(argv))
    except Exception:
        sys.exit(0)
