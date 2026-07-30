#!/usr/bin/env python3
"""Shared helpers for the grounded-copy hooks.

Both hooks exit 0 on every internal failure. A style reminder that blocks a
session start or a prompt costs more than the reminder is worth.

Flag file resolution follows the plan's two-step order:
  1. the --data-dir argv value, when it holds a real path
  2. ~/.claude/grounded-copy, a fixed path that works for a plugin
     discovered in place and survives `git pull`

Step 2 exists because ${CLAUDE_PLUGIN_DATA} may arrive empty or literal for
an @skills-dir plugin (P0.4).
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
FALLBACK_DIR = os.path.join(os.path.expanduser("~"), ".claude", "grounded-copy")


def argv_paths(argv):
    """Pull --plugin-root and --data-dir out of argv."""
    found = {"plugin_root": None, "data_dir": None}
    keys = {"--plugin-root": "plugin_root", "--data-dir": "data_dir"}
    for i, arg in enumerate(argv):
        key = keys.get(arg)
        if key and i + 1 < len(argv):
            found[key] = argv[i + 1]
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


def resolve_data_dir(value):
    """The directory holding the profile flag."""
    if value and "${" not in value and value.strip():
        return os.path.abspath(os.path.expanduser(value))
    return FALLBACK_DIR


def resolve_plugin_root(value, hook_dir):
    """The plugin root, falling back to the hooks directory's parent."""
    if value and "${" not in value and value.strip():
        return os.path.abspath(os.path.expanduser(value))
    return os.path.dirname(os.path.abspath(hook_dir))


def flag_path(data_dir):
    return os.path.join(data_dir, "profile")


def read_profile(data_dir):
    """The recorded profile, or MISSING, or INVALID.

    A symlink, an oversized file, or a value outside VALID reads as INVALID,
    so neither hook ever emits bytes it did not write. An absent flag reads as
    MISSING, which is an ordinary first run.
    """
    path = flag_path(data_dir)
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


def write_profile(data_dir, profile):
    """Record the profile. Creates the data directory on first run."""
    if profile not in VALID:
        return False
    try:
        os.makedirs(data_dir, exist_ok=True)
        path = flag_path(data_dir)
        if os.path.islink(path):
            os.unlink(path)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(profile + "\n")
        return True
    except Exception:
        return False
