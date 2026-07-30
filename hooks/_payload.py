#!/usr/bin/env python3
"""Shared helpers for the grounded-copy hooks.

Both hooks exit 0 on every internal failure. A style reminder that blocks a
session start or a prompt costs more than the reminder is worth.

The profile flag lives at <config-dir>/grounded-copy/profile, where config-dir
is $CLAUDE_CONFIG_DIR when set and ~/.claude otherwise. One fixed path, so a
hook run and a shell run reach the same file with no coordination.

${CLAUDE_PLUGIN_DATA} earns its keep for a marketplace plugin, whose
${CLAUDE_PLUGIN_ROOT} moves into a new cache directory on update. A plugin
discovered in a skills directory is read in place, so the root holds still and
that problem never arises. The flag also holds user state: a preference worth
being able to cat, edit, and grep while debugging the switch.
"""

import json
import os
import sys

VALID = ("technical", "copy", "off")
DEFAULT = "technical"
ACTIVE = ("technical", "copy")
MAX_FLAG_BYTES = 64

# read_profile returns one of these two markers in place of a profile name.
# They stay outside VALID so callers can branch on them.
MISSING = "missing"   # no flag yet: write the default and carry on
INVALID = "invalid"   # symlink, oversized, or unknown value: trust nothing


def config_dir():
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(
        os.path.expanduser("~"), ".claude"
    )


def data_dir():
    return os.path.join(config_dir(), "grounded-copy")


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


def flag_path():
    return os.path.join(data_dir(), "profile")


def read_profile():
    """The recorded profile, or MISSING, or INVALID.

    A symlink, an oversized file, or a value outside VALID reads as INVALID,
    so neither hook ever emits bytes it did not write. An absent flag reads as
    MISSING, which is an ordinary first run.
    """
    path = flag_path()
    try:
        if os.path.islink(path):
            return INVALID
        if not os.path.exists(path):
            return MISSING
        if os.path.getsize(path) > MAX_FLAG_BYTES:
            return INVALID
        with open(path, encoding="utf-8") as handle:
            value = handle.read().strip().lower()
    except Exception:
        return INVALID
    return value if value in VALID else INVALID


def write_profile(profile):
    """Record the profile. Creates the data directory on first run."""
    if profile not in VALID:
        return False
    try:
        os.makedirs(data_dir(), exist_ok=True)
        path = flag_path()
        if os.path.islink(path):
            os.unlink(path)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(profile + "\n")
        return True
    except Exception:
        return False
