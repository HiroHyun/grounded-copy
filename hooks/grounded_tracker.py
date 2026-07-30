#!/usr/bin/env python3
"""UserPromptSubmit hook: reinforce the rules and own the profile switch.

Two jobs:

  1. Parse a profile switch out of the prompt and write the flag. This hook is
     the only writer; commands/grounded.md documents the switch and writes
     nothing.
  2. Emit a one-line reminder through hookSpecificOutput.additionalContext
     while a profile is active. SessionStart injects the full ruleset once,
     and this keeps it in attention against competing per-turn injections
     from other plugins.

Usage:
    grounded_tracker.py --plugin-root DIR --data-dir DIR
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

# "chat" is the user-facing word for the technical profile.
ARG_TO_PROFILE = {
    "chat": "technical",
    "technical": "technical",
    "copy": "copy",
    "marketing": "copy",
    "off": "off",
    "stop": "off",
    "disable": "off",
}

COMMAND_NAMES = ("/grounded", "/grounded-copy:grounded")

OFF_PATTERNS = (
    re.compile(r"\b(stop|disable|deactivate|quit|exit|kill)\s+(the\s+)?grounded\b"),
    re.compile(r"\bgrounded(\s+(prose|copy|mode))?\s+(off|stop|disabled?)\b"),
    re.compile(r"\bturn\s+off\s+(the\s+)?grounded\b"),
)

ON_PATTERNS = (
    re.compile(r"\b(activate|enable|start|turn on|use|switch to)\b[^.]{0,40}\bgrounded\b"),
    re.compile(r"\bgrounded\s+(prose|copy)\s+(on|please|now)\b"),
)

QUESTION = re.compile(
    r"^(what|whats|what's|how|why|when|where|who|does|do|did|is|are|can|could|"
    r"would|should|tell me|explain)\b"
)


def parse_switch(prompt):
    """The profile this prompt selects, or None to leave the flag alone."""
    for name in COMMAND_NAMES:
        if prompt == name or prompt.startswith(name + " "):
            arg = prompt[len(name):].strip().split(" ")[0]
            if not arg:
                return _payload.DEFAULT
            return ARG_TO_PROFILE.get(arg)  # unknown arg leaves the flag alone

    if QUESTION.match(prompt):
        return None

    for pattern in OFF_PATTERNS:
        if pattern.search(prompt):
            return "off"
    for pattern in ON_PATTERNS:
        if pattern.search(prompt):
            return _payload.DEFAULT
    return None


def main(argv):
    paths = _payload.argv_paths(argv)
    data_dir = _payload.resolve_data_dir(paths["data_dir"])

    data = _payload.read_payload()
    prompt = str(data.get("prompt") or "").strip().lower()
    prompt = re.sub(r"\s+", " ", prompt)

    if prompt:
        switch = parse_switch(prompt)
        if switch:
            _payload.write_profile(data_dir, switch)

    profile = _payload.read_profile(data_dir)
    if profile == _payload.MISSING:
        profile = _payload.DEFAULT
        _payload.write_profile(data_dir, profile)
    elif profile == _payload.INVALID:
        # Emit nothing on an untrusted flag; a corrupted or symlinked file
        # never becomes a reason to inject text.
        return 0

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
