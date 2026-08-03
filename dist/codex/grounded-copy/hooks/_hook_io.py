#!/usr/bin/env python3
"""Hook transport: stdin and argv.

Kept apart from the preference and policy vocabulary. Both entrypoints call
both functions here, which is what earns the module its own file: plugin_root()
carries three resolution rules, and duplicating them across two entrypoints is
how they drift apart.

Neither entrypoint reads the event's fields, so the stdin side is a drain.
"""

import os
import sys


def utf8_streams():
    """Speak UTF-8 to the host on every platform.

    The payloads carry em dashes and the arrow in the workflow step, and a
    `copy` policy carries more. Python picks the encoding for a pipe from the
    platform, so a Windows interpreter at a legacy code page hands the host
    cp1252 bytes for those characters; a host decoding UTF-8 then reads the
    session policy mojibaked, and a character the code page cannot hold raises
    UnicodeEncodeError, which the entrypoint swallows into a silent exit 0.

    Measured: `PYTHONIOENCODING=cp1252` made a UTF-8 reader see byte 0x97 and
    return no policy at all.

    Call it before writing. `errors="replace"` keeps a payload flowing when one
    character will not encode, since a style reminder is worth less than the
    session it would break.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass


def drain_stdin():
    """Consume the hook event.

    The hook contract hands the event in on stdin. Neither entrypoint reads its
    fields, and a hook that leaves stdin unread can break the writer's pipe.
    """
    try:
        sys.stdin.read()
    except Exception:
        pass


def plugin_root(argv, hook_dir):
    """The plugin root, in order of preference.

    1. `--plugin-root DIR` from argv, which the test suite and manual runs pass
    2. $PLUGIN_ROOT from the environment (host-neutral adapter seam)
    3. $CLAUDE_PLUGIN_ROOT from the environment, which a Claude hook run inherits
    4. the hooks directory's parent, which holds for every shipped layout

    A value still carrying a literal `${` is an unsubstituted placeholder and
    falls through to the next source.
    """
    candidates = []
    for i, arg in enumerate(argv):
        if arg == "--plugin-root" and i + 1 < len(argv):
            candidates.append(argv[i + 1])
    candidates.extend((
        os.environ.get("PLUGIN_ROOT"),
        os.environ.get("CLAUDE_PLUGIN_ROOT"),
    ))

    for value in candidates:
        if value and value.strip() and "${" not in value:
            return os.path.abspath(os.path.expanduser(value))
    return os.path.dirname(os.path.abspath(hook_dir))
