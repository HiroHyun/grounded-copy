#!/usr/bin/env python3
"""Shared helpers for the grounded-copy hooks.

Both hooks exit 0 on every internal failure. A style reminder that blocks a
session start costs more than the reminder is worth.

The profile flag lives at <config-dir>/grounded-copy/profile, config-dir being
$CLAUDE_CONFIG_DIR when set and ~/.claude otherwise. One fixed path keeps hook
runs and shell runs on the same file, and keeps the preference somewhere the
user can cat and edit. references/setup.md records why ${CLAUDE_PLUGIN_DATA}
stays out of it.

resolve_profile() is the one place a flag state turns into a profile name, so
the two entry points agree on every input. It returns a name from VALID
together with the reason it chose that name, and it writes nothing.
"""

import json
import os
import sys

VALID = ("chat", "copy", "off")
DEFAULT = "chat"
ACTIVE = ("chat", "copy")
MAX_FLAG_BYTES = 64

# `technical` was the stored name for `chat` before the profiles took their
# user-facing names. A flag written by an earlier install keeps working.
LEGACY = {"technical": "chat"}

# Words accepted from `--set` and from a prompt.
ARGUMENTS = {
    "chat": "chat",
    "technical": "chat",
    "on": "chat",
    "copy": "copy",
    "marketing": "copy",
    "off": "off",
    "stop": "off",
    "disable": "off",
}

# Why resolve_profile() returned the name it returned.
RECORDED = "recorded"
ABSENT = "absent"
UNREADABLE = "unreadable"


def config_dir():
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(
        os.path.expanduser("~"), ".claude"
    )


def data_dir():
    return os.path.join(config_dir(), "grounded-copy")


def flag_path():
    return os.path.join(data_dir(), "profile")


def argv_paths(argv):
    """Pull --plugin-root out of argv."""
    found = {"plugin_root": None}
    for i, arg in enumerate(argv):
        if arg == "--plugin-root" and i + 1 < len(argv):
            found["plugin_root"] = argv[i + 1]
    return found


def read_payload():
    """Hook stdin as a dict. Malformed or absent input reads as empty."""
    try:
        raw = sys.stdin.read()
    except Exception:
        return {}
    if not raw or not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def resolve_plugin_root(value, hook_dir):
    """The plugin root, falling back to the hooks directory's parent."""
    if value and "${" not in value and value.strip():
        return os.path.abspath(os.path.expanduser(value))
    return os.path.dirname(os.path.abspath(hook_dir))


def canonical_argument(value):
    """A profile name from a --set value or a parsed prompt, or None."""
    return ARGUMENTS.get(str(value).strip().lower())


def _read_flag():
    """The recorded name, or None when the file is absent or untrusted.

    A symlink, an oversized file, or an unrecognized value reads as untrusted,
    so neither hook emits bytes it did not write.
    """
    path = flag_path()
    try:
        if os.path.islink(path):
            return None, UNREADABLE
        if not os.path.exists(path):
            return None, ABSENT
        if os.path.getsize(path) > MAX_FLAG_BYTES:
            return None, UNREADABLE
        with open(path, encoding="utf-8") as handle:
            value = handle.read().strip().lower()
    except Exception:
        return None, UNREADABLE
    value = LEGACY.get(value, value)
    if value in VALID:
        return value, RECORDED
    return None, UNREADABLE


def resolve_profile():
    """(profile, source): a name from VALID, and why. Writes nothing."""
    value, source = _read_flag()
    return (value if value else DEFAULT), source


def status_line():
    """One line naming the profile, the reason, and the resolved path."""
    profile, source = resolve_profile()
    path = flag_path()
    if source == RECORDED:
        line = "grounded profile: %s (recorded at %s)" % (profile, path)
        if profile == "off":
            line += "; run --set chat to restore"
        return line
    if source == ABSENT:
        return "grounded profile: %s (default, no flag at %s)" % (profile, path)
    return "grounded profile: %s (default, unreadable flag at %s)" % (profile, path)


def write_profile(profile):
    """Record the profile. Creates the data directory on first write."""
    if profile not in VALID:
        return False
    try:
        os.makedirs(data_dir(), exist_ok=True)
        path = flag_path()
        if os.path.islink(path):
            os.unlink(path)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(profile + "\n")
        return True
    except Exception:
        return False
