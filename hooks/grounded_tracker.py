#!/usr/bin/env python3
"""UserPromptSubmit hook: reinforce the rules and own the profile switch.

Two jobs:

  1. Parse a profile switch out of the prompt and write the flag. This script
     is the only writer, reached either as a hook or by commands/grounded.md
     through --set.
  2. Emit a one-line reminder through hookSpecificOutput.additionalContext
     while a profile is active. SessionStart injects the full ruleset once,
     and this keeps it in attention against competing per-turn injections
     from other plugins.

Usage:
    grounded_tracker.py --plugin-root DIR
    grounded_tracker.py --set chat|copy|off
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

# Plain-word switch naming a target profile, which reaches the hook even when a
# slash command does not: "switch grounded to copy", "set grounded prose to off".
NL_SWITCH = re.compile(
    r"\b(?:switch|set|change|put)\s+grounded(?:\s+prose|\s+copy)?\s+"
    r"(?:profile\s+)?(?:to|into)\s+(chat|copy|technical|marketing|off)\b"
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

    named = NL_SWITCH.search(prompt)
    if named:
        return ARG_TO_PROFILE.get(named.group(1))

    for pattern in OFF_PATTERNS:
        if pattern.search(prompt):
            return "off"
    for pattern in ON_PATTERNS:
        if pattern.search(prompt):
            return _payload.DEFAULT
    return None


def set_mode(argv):
    """--set PROFILE: write the flag from a shell run, print one line.

    commands/grounded.md calls this. A prompt starting with `/` is resolved as
    a slash command before any UserPromptSubmit event, so parsing command
    names out of the prompt cannot carry the switch on its own.
    """
    index = argv.index("--set")
    arg = argv[index + 1].strip().lower() if index + 1 < len(argv) else ""
    profile = ARG_TO_PROFILE.get(arg)
    if profile is None:
        print("grounded: unknown profile %r; choose chat, copy, or off" % arg)
        return 0
    if _payload.write_profile(profile):
        print("grounded profile: %s (%s)" % (profile, _payload.flag_path()))
    else:
        print("grounded: write failed at " + _payload.flag_path())
    return 0


def main(argv):
    if "--set" in argv:
        return set_mode(argv)

    data = _payload.read_payload()
    prompt = str(data.get("prompt") or "").strip().lower()
    prompt = re.sub(r"\s+", " ", prompt)

    if prompt:
        switch = parse_switch(prompt)
        if switch:
            _payload.write_profile(switch)

    profile = _payload.read_profile()
    if profile == _payload.MISSING:
        profile = _payload.DEFAULT
        _payload.write_profile(profile)
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
