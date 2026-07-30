#!/usr/bin/env python3
"""UserPromptSubmit hook: reinforce the rules and own the profile switch.

Emits a one-line reminder while a profile is active, which holds against the
per-turn injections other plugins make. Also the only writer of the flag,
reached either as a hook or through --set.

A prompt switches the profile when its whole text is a control instruction.
An unanchored search matched the words wherever they appeared, so a quoted
error string, a pasted line, or a note about this plugin's own documentation
each wrote a persistent value that nothing in the transcript reported.

Usage:
    grounded_tracker.py --plugin-root DIR
    grounded_tracker.py --set chat|copy|off
    grounded_tracker.py --status
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _payload  # noqa: E402

REMINDER = (
    "GROUNDED PROSE ACTIVE ({profile}). State what the subject is or does. "
    "No negation-contrast, no era-ending, no competitor contrast, no hype "
    "register. Code and errors verbatim."
)

# A prompt longer than this carries content around the words, whatever else it
# holds, so no control form can match it.
MAX_CONTROL_CHARS = 64

NAME = r"(chat|copy|technical|marketing|off|on|stop|disable)"

# Each form matches a whole prompt. A trailing `?` falls outside every one of
# them, which leaves questions about the switch as questions.
CONTROL_FORMS = (
    re.compile(r"^grounded(?:\s+(?:prose|copy|mode))?\s+" + NAME + r"$"),
    re.compile(
        r"^(?:switch|set|change|put)\s+grounded(?:\s+prose)?"
        r"(?:\s+profile)?\s+(?:to|into)\s+" + NAME + r"$"
    ),
    re.compile(
        r"^(?:stop|disable|deactivate|turn\s+off)\s+(?:the\s+)?"
        r"grounded(?:\s+(?:prose|copy|mode))?$"
    ),
    re.compile(
        r"^(?:activate|enable|start)\s+(?:the\s+)?grounded(?:\s+prose)?$"
    ),
)

# The form each pattern selects when it names no profile of its own.
IMPLIED = {2: "off", 3: _payload.DEFAULT}


def parse_switch(prompt):
    """The profile this prompt selects, or None to leave the flag alone."""
    if not prompt or len(prompt) > MAX_CONTROL_CHARS:
        return None
    for index, pattern in enumerate(CONTROL_FORMS):
        match = pattern.match(prompt)
        if not match:
            continue
        if match.groups():
            return _payload.canonical_argument(match.group(1))
        return IMPLIED[index]
    return None


def set_mode(argv):
    """--set PROFILE: write the flag from a shell run, print one line.

    commands/grounded.md calls this. A `/` prompt is resolved as a slash
    command before any UserPromptSubmit event, so the command file is the only
    path the slash form takes.
    """
    index = argv.index("--set")
    raw = argv[index + 1] if index + 1 < len(argv) else ""
    if not raw.strip():
        print(_payload.status_line())
        return 0
    profile = _payload.canonical_argument(raw)
    if profile is None:
        print(
            "grounded: unknown profile %r; choose chat, copy, or off"
            % raw.strip().lower()
        )
        return 0
    if _payload.write_profile(profile):
        print(_payload.status_line())
    else:
        print("grounded: write failed at " + _payload.flag_path())
    return 0


def main(argv):
    if "--status" in argv:
        print(_payload.status_line())
        return 0
    if "--set" in argv:
        return set_mode(argv)

    data = _payload.read_payload()
    raw = data.get("prompt")
    prompt = re.sub(r"\s+", " ", raw.strip().lower()) if isinstance(raw, str) else ""

    switch = parse_switch(prompt)
    if switch:
        _payload.write_profile(switch)

    profile, _source = _payload.resolve_profile()
    if profile not in _payload.ACTIVE:
        return 0

    sys.stdout.write(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": REMINDER.format(profile=profile),
        }
    }))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception:
        sys.exit(0)
