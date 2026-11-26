#!/usr/bin/env python3
"""Generate and verify the Antigravity grounded-copy plugin.

Antigravity loads a native plugin from a directory carrying plugin.json,
hooks.json at the plugin root, and skills/. This builder mirrors the canonical
skill and shared hook libraries into dist/antigravity/grounded-copy, generates
Antigravity's protojson hook entrypoints and grounded-profile controller skill,
and verifies the tree byte-for-byte with --check.

Antigravity's PostToolUse hook expects an empty {} response and cannot return
findings to the agent, so the save gate runs in PreToolUse instead: it inspects
the proposed write or edit in memory before it hits disk, keeps sentences the
user typed in the session transcript, and denies only on agent-written
findings.
"""

import json
import os
import sys

import build_codex_adapter as codex

ADAPTER = os.path.join("dist", "antigravity", "grounded-copy")

MANIFEST = json.dumps({
    "name": "grounded-copy",
    "displayName": "Grounded Copy",
    "version": codex.VERSION,
    "description": "Help AI say clearly and get to the point.",
    "author": {"name": "HiroHyun", "url": "https://github.com/HiroHyun"},
    "homepage": "https://github.com/HiroHyun/grounded-copy",
    "repository": "https://github.com/HiroHyun/grounded-copy",
    "logo": "assets/logo.png",
    "suggestedPrompts": [
        "Explain how compound interest works.",
        "Summarize this document.",
        "Write a product description from these facts.",
    ],
}, indent=2) + "\n"

# Antigravity runs hook commands via `cmd /c` on Windows and `sh -c` on Unix,
# with the working directory set to the plugin folder. Relative paths keep
# spaces or shell metacharacters in the install directory off the command line.
# All three Antigravity entrypoints exit 0, so Windows finishes on the first
# branch and Unix falls through to run.sh.
def _hook_cmd(script):
    return "cmd /d /c hooks\\run.cmd %s || sh ./hooks/run.sh %s" % (script, script)


HOOKS = json.dumps({
    "grounded-copy": {
        "SessionStart": [
            {
                "type": "command",
                "command": _hook_cmd("grounded_activate.py"),
                "timeout": 10,
            }
        ],
        "PreInvocation": [
            {
                "type": "command",
                "command": _hook_cmd("grounded_tracker.py"),
                "timeout": 10,
            }
        ],
        "PreToolUse": [
            {
                "matcher": "write_file|edit_file|write_to_file|replace_file_content|multi_replace_file_content",
                "hooks": [
                    {
                        "type": "command",
                        "command": _hook_cmd("grounded_gate.py"),
                        "timeout": 15,
                    }
                ],
            }
        ],
    }
}, indent=2) + "\n"

# Antigravity PreToolUse is fail-closed, so when no Python 3 resolves the
# launcher still emits {"decision":"allow"} for grounded_gate.py and {} for
# the lifecycle hooks.
RUN_SH = """#!/bin/sh
# Resolve a Python 3 interpreter once, then run the named Antigravity hook.
hookdir=${0%/*}
[ "$hookdir" = "$0" ] && hookdir=.

case "$1" in
    grounded_activate.py) script=grounded_activate.py; fallback='{}' ;;
    grounded_tracker.py) script=grounded_tracker.py; fallback='{}' ;;
    grounded_gate.py) script=grounded_gate.py; fallback='{"decision":"allow"}' ;;
    *) printf '{}\\n'; exit 0 ;;
esac
shift

for candidate in python python3; do
    if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)' >/dev/null 2>&1; then
        exec "$candidate" "$hookdir/$script" "$@"
    fi
done

printf '%s\\n' "$fallback"
exit 0
"""

RUN_CMD = (
    "@echo off\r\n"
    "rem Run the named Antigravity hook once with python or python3.\r\n"
    "setlocal\r\n"
    "set \"HOOKDIR=%~dp0\"\r\n"
    "\r\n"
    "set \"SCRIPT=\"\r\n"
    "if /i \"%~1\"==\"grounded_activate.py\" set \"SCRIPT=grounded_activate.py\"\r\n"
    "if /i \"%~1\"==\"grounded_tracker.py\" set \"SCRIPT=grounded_tracker.py\"\r\n"
    "if /i \"%~1\"==\"grounded_gate.py\" set \"SCRIPT=grounded_gate.py\"\r\n"
    "if not defined SCRIPT (\r\n"
    "    echo {}\r\n"
    "    exit /b 0\r\n"
    ")\r\n"
    "\r\n"
    "python \"%HOOKDIR%%SCRIPT%\" %2 %3 %4 %5 %6 %7 %8 %9\r\n"
    "if not errorlevel 9009 exit /b %ERRORLEVEL%\r\n"
    "python3 \"%HOOKDIR%%SCRIPT%\" %2 %3 %4 %5 %6 %7 %8 %9\r\n"
    "if not errorlevel 9009 exit /b %ERRORLEVEL%\r\n"
    "if /i \"%SCRIPT%\"==\"grounded_gate.py\" (\r\n"
    "    echo {\"decision\":\"allow\"}\r\n"
    ") else (\r\n"
    "    echo {}\r\n"
    ")\r\n"
    "exit /b 0\r\n"
)

ACTIVATE = r'''#!/usr/bin/env python3
"""Antigravity SessionStart hook: inject the session policy as a system step."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _hook_io  # noqa: E402
import _policy  # noqa: E402
import _preference  # noqa: E402

PREFERENCE_PATH = os.path.join(
    os.environ.get("ANTIGRAVITY_CONFIG_DIR") or os.path.join(
        os.path.expanduser("~"), ".gemini", "config"
    ),
    "grounded-copy",
    "profile",
)
SWITCH_HINT = "grounded-profile (chat, copy, or off)"


def main(argv):
    _hook_io.utf8_streams()
    hook_dir = os.path.dirname(os.path.abspath(__file__))
    root = _hook_io.plugin_root(argv, hook_dir)

    if "--self-test" in argv:
        return _policy.self_test(root)

    _hook_io.drain_stdin()

    path = _hook_io.preference_arg(argv, PREFERENCE_PATH)
    profile, _source = _preference.resolve_preference(path)
    if profile not in _preference.ACTIVE:
        sys.stdout.write("{}\n")
        return 0

    skill = _policy.read_skill(root)
    if not skill:
        sys.stdout.write("{}\n")
        return 0

    policy = _policy.session_policy(skill, profile, SWITCH_HINT)
    sys.stdout.write(json.dumps({
        "injectSteps": [
            {"systemMessage": {"systemMessage": policy}},
        ],
    }) + "\n")
    return 0


if __name__ == "__main__":
    argv = sys.argv[1:]
    if "--self-test" in argv:
        sys.exit(main(argv))
    try:
        sys.exit(main(argv))
    except Exception:
        sys.stdout.write("{}\n")
        sys.exit(0)
'''

TRACKER = r'''#!/usr/bin/env python3
"""Antigravity PreInvocation hook, and the profile control CLI.

PreInvocation fires before every model call in a turn; emitting only on
invocationNum == 0 injects the turn reminder once per user prompt so it does
not pile up across tool-call steps.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _hook_io  # noqa: E402
import _policy  # noqa: E402
import _preference  # noqa: E402

PREFERENCE_PATH = os.path.join(
    os.environ.get("ANTIGRAVITY_CONFIG_DIR") or os.path.join(
        os.path.expanduser("~"), ".gemini", "config"
    ),
    "grounded-copy",
    "profile",
)
RESTORE_HINT = "grounded-profile (chat)"

EXIT_OK = 0
EXIT_PERSISTENCE = 1
EXIT_REJECTED = 2
CONTROL_FLAGS = ("--set", "--status")


def set_mode(argv, hook_dir):
    index = argv.index("--set")
    raw = argv[index + 1] if index + 1 < len(argv) else ""
    path = _hook_io.preference_arg(argv, PREFERENCE_PATH)
    if not raw.strip():
        print(_preference.status_line(path, RESTORE_HINT))
        return EXIT_OK

    profile = _preference.canonical_argument(raw)
    if profile is None:
        print(
            "grounded: unknown profile %r; choose chat, copy, or off"
            % raw.strip().lower()
        )
        return EXIT_REJECTED

    ok, detail = _preference.write_preference(profile, path)
    if not ok:
        print(detail)
        return EXIT_PERSISTENCE

    print(_preference.status_line(path, RESTORE_HINT))
    print()
    skill = _policy.read_skill(_hook_io.plugin_root(argv, hook_dir))
    source = "recorded at " + _preference.preference_path(path)
    print(_policy.governing_directive(skill, profile, source))
    return EXIT_OK


def main(argv):
    _hook_io.utf8_streams()
    hook_dir = os.path.dirname(os.path.abspath(__file__))

    if "--set" in argv:
        return set_mode(argv, hook_dir)
    if "--status" in argv:
        path = _hook_io.preference_arg(argv, PREFERENCE_PATH)
        print(_preference.status_line(path, RESTORE_HINT))
        return EXIT_OK

    event = _hook_io.read_event() or {}
    if event.get("invocationNum", 0) != 0:
        sys.stdout.write("{}\n")
        return EXIT_OK

    profile, _source = _preference.resolve_preference(
        _hook_io.preference_arg(argv, PREFERENCE_PATH)
    )
    if profile not in _preference.ACTIVE:
        sys.stdout.write("{}\n")
        return EXIT_OK

    sys.stdout.write(json.dumps({
        "injectSteps": [
            {"systemMessage": {"systemMessage": _policy.turn_reminder(profile)}},
        ],
    }) + "\n")
    return EXIT_OK


if __name__ == "__main__":
    argv = sys.argv[1:]
    if any(flag in argv for flag in CONTROL_FLAGS):
        sys.exit(main(argv))
    try:
        sys.exit(main(argv))
    except Exception:
        sys.stdout.write("{}\n")
        sys.exit(0)
'''

GATE = r'''#!/usr/bin/env python3
"""Antigravity PreToolUse hook: check proposed prose writes before they save.

Antigravity's PostToolUse expects {} and cannot send findings back to the
agent, so the gate runs in PreToolUse. PreToolUse is fail-closed: every clean,
out-of-scope, off-profile, or errored path returns {"decision": "allow"}.
"""

import difflib
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _gate_core  # noqa: E402
import _hook_io  # noqa: E402
import _preference  # noqa: E402

PREFERENCE_PATH = os.path.join(
    os.environ.get("ANTIGRAVITY_CONFIG_DIR") or os.path.join(
        os.path.expanduser("~"), ".gemini", "config"
    ),
    "grounded-copy",
    "profile",
)

_USER_REQUEST = re.compile(r"<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>", re.S)
_STRIP_META = re.compile(
    r"<(?:ADDITIONAL_METADATA|USER_SETTINGS_CHANGE)\b[^>]*>.*?"
    r"</(?:ADDITIONAL_METADATA|USER_SETTINGS_CHANGE)>",
    re.S,
)


def _allow():
    sys.stdout.write('{"decision": "allow"}\n')
    return 0


def _resolve_path(path, cwd):
    if not isinstance(path, str) or not path.strip():
        return ""
    if os.path.isabs(path) or not cwd:
        return path
    return os.path.join(cwd, path)


def _changed_offsets(old_text, new_text):
    """0-based line indices inside new_text that differ from old_text."""
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()
    changed = set()
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False)
    for tag, _i1, _i2, j1, j2 in matcher.get_opcodes():
        if tag in ("insert", "replace"):
            changed.update(range(j1, j2))
    return changed


def _apply_replacements(path, pairs):
    """Apply (target, replacement) pairs in memory; return (text, added_lines)."""
    existing = None
    if os.path.isfile(path):
        try:
            with io.open(path, encoding="utf-8", errors="replace") as handle:
                existing = handle.read()
        except OSError:
            existing = None

    if existing is not None:
        virtual = existing
        applied = True
        for target, replacement in pairs:
            if not target or target not in virtual:
                applied = False
                break
            virtual = virtual.replace(target, replacement)
        if applied:
            added = {off + 1 for off in _changed_offsets(existing, virtual)}
            return virtual, added

    # Fallback when the file is absent or target does not match on disk:
    # check only the changed replacement lines.
    chunks = []
    added = set()
    cursor = 1
    for target, replacement in pairs:
        lines = replacement.splitlines()
        offsets = _changed_offsets(target, replacement) if target else set(range(len(lines)))
        added.update(cursor + off for off in offsets)
        chunks.append(replacement)
        cursor += max(len(lines), 1)
    return "\n".join(chunks), added


def _proposed_edit(event):
    """Return (path, virtual_text, checked_lines_or_None) for a write/edit call."""
    tool_call = event.get("toolCall") or {}
    name = tool_call.get("name") or ""
    args = tool_call.get("args") or {}
    cwd = event.get("cwd") or ""

    if name in ("write_file", "write_to_file"):
        path = _resolve_path(args.get("Path") or args.get("TargetFile"), cwd)
        content = args.get("Content")
        if content is None:
            content = args.get("CodeContent")
        if not path or not isinstance(content, str):
            return "", "", None
        if args.get("Append") and os.path.isfile(path):
            try:
                with io.open(path, encoding="utf-8", errors="replace") as handle:
                    existing = handle.read()
                start_line = existing.count("\n") + 1
                combined = existing + content
                end_line = combined.count("\n") + 1
                return path, combined, set(range(start_line, end_line + 1))
            except OSError:
                pass
        return path, content, None

    if name in ("edit_file", "replace_file_content"):
        path = _resolve_path(args.get("Path") or args.get("TargetFile"), cwd)
        target = args.get("Target")
        if target is None:
            target = args.get("TargetContent")
        replacement = args.get("Replacement")
        if replacement is None:
            replacement = args.get("ReplacementContent")
        if not path or not isinstance(replacement, str):
            return "", "", None
        text, lines = _apply_replacements(path, [(target or "", replacement)])
        return path, text, lines

    if name == "multi_replace_file_content":
        path = _resolve_path(args.get("TargetFile") or args.get("Path"), cwd)
        chunks = args.get("ReplacementChunks") or []
        pairs = [
            (c.get("TargetContent") or "", c.get("ReplacementContent"))
            for c in chunks
            if isinstance(c, dict) and isinstance(c.get("ReplacementContent"), str)
        ]
        if not path or not pairs:
            return "", "", None
        text, lines = _apply_replacements(path, pairs)
        return path, text, lines

    return "", "", None


def _antigravity_text(row):
    """Typed user prompt text from an Antigravity transcript row, or ''."""
    if row.get("type") != "USER_INPUT" or row.get("source") != "USER_EXPLICIT":
        return ""
    content = row.get("content")
    if not isinstance(content, str) or not content.strip():
        return ""
    match = _USER_REQUEST.search(content)
    if match:
        return match.group(1)
    return _STRIP_META.sub("", content).strip()


def typed_messages(path):
    messages = []
    try:
        with io.open(path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if '"USER_EXPLICIT"' not in line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if isinstance(row, dict):
                    text = _antigravity_text(row)
                    if text:
                        messages.append(text)
    except (OSError, TypeError):
        pass
    return messages


def main(argv):
    _hook_io.utf8_streams()
    event = _hook_io.read_event() or {}
    path, text, checked_lines = _proposed_edit(event)
    if not path or not _gate_core.in_scope(path):
        return _allow()

    profile, _source = _preference.resolve_preference(
        _hook_io.preference_arg(argv, PREFERENCE_PATH)
    )
    if profile not in _preference.ACTIVE:
        return _allow()

    hook_dir = os.path.dirname(os.path.abspath(__file__))
    cl = _gate_core._checker(_hook_io.plugin_root(argv, hook_dir))
    found = cl.scan_text(text, profile)
    if checked_lines is not None:
        found = [finding for finding in found if finding[0] in checked_lines]
    if not found:
        return _allow()

    typed = typed_messages(event.get("transcriptPath"))
    report, kept = _gate_core.split_kept(cl, text, found, typed)
    if not report:
        return _allow()

    lines = ["grounded-copy gate blocked save to %s" % path]
    lines += cl.report(path, report)
    if kept:
        lines.append("%d sentence(s) the user wrote stay as written." % len(kept))
    lines.append("Rewrite each flagged sentence, then save again. "
                 "Do not edit the linter.")
    sys.stdout.write(json.dumps({
        "decision": "deny",
        "reason": "\n".join(lines),
    }) + "\n")
    return 0


if __name__ == "__main__":
    try:
        code = main(sys.argv[1:])
    except Exception:
        code = _allow()
    sys.exit(code)
'''

PROFILE_SKILL = """---
name: grounded-profile
description: Show or change the grounded-copy writing mode when the user asks for chat, copy, off, or status.
---

# grounded-profile

Use this skill when the user explicitly asks to view or change the grounded-copy writing mode.

Run `python scripts/profile.py <operation>` (or `python3` if `python` is unavailable) from this skill directory. Accept exactly `chat`, `copy`, `off`, or `status` as the operation.

`chat` covers everyday interaction and ordinary document processing. `copy` is for product pages, marketing copy, and similar text. `off` stops the rules and reminders. `status` shows the saved setting.

The setting is saved at `$ANTIGRAVITY_CONFIG_DIR/grounded-copy/profile`, using `~/.gemini/config` as the default directory. After a successful change, report the status and apply the printed instructions from this turn forward. If saving fails, report the error.
"""

PROFILE_SCRIPT = r'''#!/usr/bin/env python3
"""Explicit Antigravity profile controller."""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS = os.path.join(ROOT, "..", "..", "hooks")
sys.path.insert(0, os.path.abspath(HOOKS))
import _policy  # noqa: E402
import _preference  # noqa: E402

OPS = {"chat": "chat", "copy": "copy", "off": "off", "status": "status"}
EXIT_PERSISTENCE = 1
EXIT_REJECTED = 2
RESTORE_HINT = "grounded-profile (chat)"
PREFERENCE_PATH = os.path.join(
    os.environ.get("ANTIGRAVITY_CONFIG_DIR") or os.path.join(
        os.path.expanduser("~"), ".gemini", "config"
    ),
    "grounded-copy",
    "profile",
)


def main(argv):
    raw = argv[0].strip().lower() if argv else "status"
    operation = OPS.get(raw)
    if operation is None or len(argv) != 1:
        print("grounded: choose exactly chat, copy, off, or status")
        return EXIT_REJECTED
    if operation == "status":
        print(_preference.status_line(PREFERENCE_PATH, RESTORE_HINT))
        return 0
    ok, detail = _preference.write_preference(operation, PREFERENCE_PATH)
    if not ok:
        print(detail)
        return EXIT_PERSISTENCE
    print(_preference.status_line(PREFERENCE_PATH, RESTORE_HINT))
    print()
    root = os.environ.get("PLUGIN_ROOT") or os.path.abspath(os.path.join(ROOT, "..", ".."))
    skill = _policy.read_skill(root)
    source = "recorded at " + _preference.preference_path(PREFERENCE_PATH)
    print(_policy.governing_directive(skill, operation, source))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
'''

README = """# grounded-copy for Antigravity

Help AI say clearly and get to the point.

This plugin gives Antigravity the grounded-copy writing rules at session start, a short reminder on each prompt, a check on prose files before the agent saves them, and the `grounded-profile` skill to switch writing modes.

## Install

From a clone of the repository, install the bundle with the Antigravity CLI:

    agy plugin install ./dist/antigravity/grounded-copy

Or copy `dist/antigravity/grounded-copy` into `~/.gemini/config/plugins/grounded-copy` (or `.agents/plugins/grounded-copy` inside a workspace).

## Writing mode

Ask the agent to use `grounded-profile` with `status`, `chat`, `copy`, or `off`. Choose `chat` for everyday interaction and ordinary documents, `copy` for product pages and marketing copy, or `off` to turn the rules off. Your choice stays saved after a restart.

The setting lives at `$ANTIGRAVITY_CONFIG_DIR/grounded-copy/profile`, or `~/.gemini/config/grounded-copy/profile` by default.

Read the [setup guide](skills/grounded-copy/references/setup.md) for details and the [pattern guide](skills/grounded-copy/references/patterns.md) for examples.

## Package maintenance

This directory is generated by `scripts/build_antigravity_adapter.py` in the repository. Edit the source files there, run the builder, and commit the generated files. The builder's `--check` option reports differences, missing files, and unexpected files.

## License

[AGPL-3.0-only](LICENSE). [NOTICE](NOTICE) carries the copyright.
"""


def payloads():
    items = codex._skill_payloads()
    items.append(codex._copy_source("assets/logo.png", "assets/logo.png"))
    items.append(codex._copy_source("LICENSE", "LICENSE"))
    items.append(codex._copy_source("NOTICE", "NOTICE"))
    for name in ("_hook_io.py", "_policy.py", "_preference.py"):
        items.append(codex._copy_source("hooks/" + name, "hooks/" + name))
    items.append(codex._copy_source("hooks/grounded_gate.py", "hooks/_gate_core.py"))
    items.extend([
        ("hooks/run.sh", RUN_SH.encode()),
        ("hooks/run.cmd", RUN_CMD.encode()),
        ("hooks/grounded_activate.py", ACTIVATE.encode()),
        ("hooks/grounded_tracker.py", TRACKER.encode()),
        ("hooks/grounded_gate.py", GATE.encode()),
        ("hooks.json", HOOKS.encode()),
        ("plugin.json", MANIFEST.encode()),
        ("skills/grounded-profile/SKILL.md", PROFILE_SKILL.encode()),
        ("skills/grounded-profile/scripts/profile.py", PROFILE_SCRIPT.encode()),
        ("README.md", README.encode()),
    ])
    return [(os.path.normpath(os.path.join(ADAPTER, dest)), data) for dest, data in items]


if __name__ == "__main__":
    items = payloads()
    if "--check" in sys.argv[1:]:
        sys.exit(codex.check(ADAPTER, items, "antigravity"))
    sys.exit(codex.build(ADAPTER, items))
