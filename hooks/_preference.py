#!/usr/bin/env python3
"""The profile preference: the value stored on disk.

The preference lives at <config-dir>/grounded-copy/profile, config-dir being
$CLAUDE_CONFIG_DIR when set and ~/.claude otherwise. One fixed path keeps hook
runs and shell runs on the same file, and keeps the preference somewhere the
user can cat and edit. skills/grounded-copy/references/setup.md records why
${CLAUDE_PLUGIN_DATA} stays out of it.

This module is the sole writer of the preference, and the `--set` path of
grounded_tracker.py is its only caller. resolve_preference() is read-only, and
both hooks are read-only.

Transport stays outside this module: it reads no stdin and parses no argv.
"""

import os

VALID = ("chat", "copy", "off")
DEFAULT = "chat"
ACTIVE = ("chat", "copy")
MAX_PREFERENCE_BYTES = 64

# `technical` was the stored name for `chat` before the profiles took their
# user-facing names. A preference written by an earlier install keeps working.
LEGACY = {"technical": "chat"}

# Words `--set` accepts: the three profile names, plus `technical` for the
# legacy stored value and `marketing` for the register `copy` carries. `on`,
# `stop`, and `disable` came out with the natural-language switch that used
# them; nothing documented or tested them afterwards.
ARGUMENTS = {
    "chat": "chat",
    "technical": "chat",
    "copy": "copy",
    "marketing": "copy",
    "off": "off",
}

# The Claude command that restores an active profile. A copied entrypoint
# passes its own host's verb instead.
CLAUDE_RESTORE = "--set chat"

# Why resolve_preference() returned the name it returned.
RECORDED = "recorded"
ABSENT = "absent"
UNREADABLE = "unreadable"


def config_dir():
    """Return Claude's config directory for the canonical entrypoints."""
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(
        os.path.expanduser("~"), ".claude"
    )


def data_dir():
    return os.path.join(config_dir(), "grounded-copy")


def preference_path(path=None):
    """Resolve an explicit profile file or Claude's canonical default."""
    if path is not None:
        return os.path.abspath(os.path.expanduser(os.fspath(path)))
    return os.path.join(data_dir(), "profile")


def canonical_argument(value):
    """A profile name from a `--set` value, or None."""
    return ARGUMENTS.get(str(value).strip().lower())


def _read_preference(path=None):
    """The recorded name, or None when the file is absent or untrusted.

    A symlink, an oversized file, or an unrecognized value reads as untrusted,
    so neither hook emits bytes it did not write.
    """
    path = preference_path(path)
    try:
        if os.path.islink(path):
            return None, UNREADABLE
        if not os.path.exists(path):
            return None, ABSENT
        if os.path.getsize(path) > MAX_PREFERENCE_BYTES:
            return None, UNREADABLE
        with open(path, encoding="utf-8") as handle:
            value = handle.read().strip().lower()
    except Exception:
        return None, UNREADABLE
    value = LEGACY.get(value, value)
    if value in VALID:
        return value, RECORDED
    return None, UNREADABLE


def resolve_preference(path=None):
    """(profile, source): a name from VALID, and why. Read-only."""
    value, source = _read_preference(path)
    return (value if value else DEFAULT), source


def status_line(path=None, restore=None):
    """One line naming the profile, the reason, and the resolved path.

    ``restore`` is the host's command for returning to an active profile. The
    Claude flag is the default; the Codex entrypoint passes its own verb.
    """
    profile, source = resolve_preference(path)
    path = preference_path(path)
    if source == RECORDED:
        line = "grounded profile: %s (recorded at %s)" % (profile, path)
        if profile == "off":
            line += "; run %s to restore" % (restore or CLAUDE_RESTORE)
        return line
    if source == ABSENT:
        return "grounded profile: %s (default, no preference at %s)" % (
            profile, path
        )
    return "grounded profile: %s (default, unreadable preference at %s)" % (
        profile, path
    )


def write_preference(profile, path=None):
    """Record the preference. Returns (ok, detail).

    The write is followed by a read-back through _read_preference(), so a write
    that lands somewhere the resolver cannot use reports failure here instead
    of resolving stale later. Creates the data directory on first write.

    A symlink at the path is reported, never removed. _read_preference() reads
    one as untrusted, so the link is already inert, and deleting a file the user
    put there reaches past what this function owns.
    """
    if profile not in VALID:
        return False, "grounded: refusing to record %r" % (profile,)
    path = preference_path(path)
    if os.path.islink(path):
        return False, (
            "grounded: %s is a symlink, which resolve_preference() reads as "
            "unreadable. Remove it and run --set again." % path
        )
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # Replace a same-directory temporary file so readers never observe a
        # partially written profile. The symlink check above remains the guard
        # that prevents replacing a user-owned link.
        import tempfile
        fd, temporary = tempfile.mkstemp(prefix=".profile-", dir=os.path.dirname(path))
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(profile + "\n")
            os.replace(temporary, path)
        finally:
            try:
                os.unlink(temporary)
            except OSError:
                pass
    except Exception as exc:
        return False, "grounded: write failed at %s: %s" % (path, exc)

    stored, source = _read_preference(path)
    if stored != profile:
        return False, (
            "grounded: wrote %s at %s, read back %s (%s)"
            % (profile, path, stored, source)
        )
    return True, ""
