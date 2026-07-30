#!/usr/bin/env python3
"""Shared helpers for the grounded-copy hooks.

Both hooks exit 0 on every internal failure. A style reminder that blocks a
session start costs more than the reminder is worth.

The profile flag lives at <config-dir>/grounded-copy/profile, config-dir being
$CLAUDE_CONFIG_DIR when set and ~/.claude otherwise. One fixed path keeps hook
runs and shell runs on the same file, and keeps the preference somewhere the
user can cat and edit. references/setup.md records why ${CLAUDE_PLUGIN_DATA}
stays out of it.
"""

import json
import os
import sys

VALID = ("technical", "copy", "off")
DEFAULT = "technical"
ACTIVE = ("technical", "copy")
MAX_FLAG_BYTES = 64

# Markers read_profile returns in place of a name; outside VALID so callers
# can branch on them.
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

    A symlink, an oversized file, or an unknown value reads as INVALID, so
    neither hook emits bytes it did not write.
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
