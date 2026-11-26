#!/usr/bin/env python3
"""Generate and verify the Gemini CLI grounded-copy extension.

Gemini CLI loads an extension from a directory carrying gemini-extension.json,
hooks/hooks.json, commands/*.toml, and skills/. This builder mirrors the
canonical skill and shared hook libraries into dist/gemini/grounded-copy,
rewrites the lifecycle hook seams for Gemini CLI's SessionStart and BeforeAgent
events, ships an AfterTool save gate for write_file and replace, adds the
/grounded custom command, and verifies the tree byte-for-byte with --check.
"""

import json
import os
import sys

import build_codex_adapter as codex

ADAPTER = os.path.join("dist", "gemini", "grounded-copy")

MANIFEST = json.dumps({
    "name": "grounded-copy",
    "version": codex.VERSION,
    "description": "Help AI say clearly and get to the point.",
}, indent=2) + "\n"

GEMINI_PREFERENCE = (
    b'PREFERENCE_PATH = os.path.join(\n'
    b'    os.environ.get("GEMINI_CLI_HOME") or os.path.expanduser("~"),\n'
    b'    ".gemini",\n'
    b'    "grounded-copy",\n'
    b'    "profile",\n'
    b')'
)
GEMINI_SWITCH = b'SWITCH_HINT = "/grounded chat|copy|off"'
GEMINI_RESTORE = b'RESTORE_HINT = "/grounded chat"'

SEAMS = {
    "grounded_activate.py": (
        (b'PREFERENCE_PATH = None', GEMINI_PREFERENCE),
        (b'SWITCH_HINT = None', GEMINI_SWITCH),
    ),
    "grounded_tracker.py": (
        (b'PREFERENCE_PATH = None', GEMINI_PREFERENCE),
        (b'RESTORE_HINT = None', GEMINI_RESTORE),
        (b'"hookEventName": "UserPromptSubmit"', b'"hookEventName": "BeforeAgent"'),
    ),
}


def _gemini_entrypoint(name):
    payload = codex._read(os.path.join(codex.REPO_ROOT, "hooks", name))
    if payload is None:
        raise IOError("unreadable source: hooks/" + name)
    for anchor, replacement in SEAMS[name]:
        if anchor not in payload:
            raise IOError(
                "seam %r absent from hooks/%s" % (anchor.decode(), name)
            )
        payload = payload.replace(anchor, replacement)
    return payload


def _polyglot_launcher(script):
    """Polyglot .cmd/.sh launcher matching hooks/claude_*.cmd.

    Gemini CLI runs hooks in PowerShell on Windows and bash on Unix, and
    substitutes ${extensionPath} into hooks/hooks.json. Passing
    "${extensionPath}" as the argument lets bash/zsh resolve run.sh while
    cmd.exe uses %~dp0 beside this launcher.
    """
    return (
        ":<<'BATCH'\r\n"
        "@rem Gemini CLI hook launcher for %s.\r\n"
        "@\"%%~dp0run.cmd\" %s\r\n"
        "BATCH\r\n"
        "exec sh \"$1/hooks/run.sh\" %s #\r\n"
    ) % (script, script, script)


# Gemini CLI hook timeouts are in milliseconds.
HOOKS = json.dumps({
    "hooks": {
        "SessionStart": [
            {
                "hooks": [
                    {
                        "name": "grounded-copy-activate",
                        "description": "Load grounded-copy writing rules at session start",
                        "type": "command",
                        "command": '. "${extensionPath}/hooks/gemini_activate.cmd" "${extensionPath}"',
                        "timeout": 5000,
                    }
                ]
            }
        ],
        "BeforeAgent": [
            {
                "hooks": [
                    {
                        "name": "grounded-copy-reminder",
                        "description": "Add the grounded-copy turn reminder before each prompt",
                        "type": "command",
                        "command": '. "${extensionPath}/hooks/gemini_tracker.cmd" "${extensionPath}"',
                        "timeout": 5000,
                    }
                ]
            }
        ],
        "AfterTool": [
            {
                "matcher": "write_file|replace",
                "hooks": [
                    {
                        "name": "grounded-copy-gate",
                        "description": "Check prose files after the agent saves them",
                        "type": "command",
                        "command": '. "${extensionPath}/hooks/gemini_gate.cmd" "${extensionPath}"',
                        "timeout": 10000,
                    }
                ],
            }
        ],
    }
}, indent=2) + "\n"

GATE = r'''#!/usr/bin/env python3
"""Gemini CLI AfterTool hook: check what write_file or replace just saved.

Returns structured JSON on stdout with exit code 0 per the Gemini CLI hook
contract: {"decision": "deny", "reason": ...} on findings, {"systemMessage":
...} when only user-typed sentences matched, and {} otherwise.
"""

import difflib
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _gate_core  # noqa: E402
import _hook_io  # noqa: E402
import _preference  # noqa: E402

PREFERENCE_PATH = os.path.join(
    os.environ.get("GEMINI_CLI_HOME") or os.path.expanduser("~"),
    ".gemini",
    "grounded-copy",
    "profile",
)


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


def _saved_target(event):
    """Return (path, old_string_or_None, new_string_or_None) for a save call."""
    response = event.get("tool_response")
    if isinstance(response, dict) and response.get("error"):
        return "", None, None
    tool_input = event.get("tool_input") or {}
    path = tool_input.get("file_path") or tool_input.get("path")
    if not isinstance(path, str) or not path.strip():
        return "", None, None
    cwd = event.get("cwd") or ""
    if not os.path.isabs(path) and cwd:
        path = os.path.join(cwd, path)
    old_str = tool_input.get("old_string")
    new_str = tool_input.get("new_string")
    if isinstance(new_str, str):
        return path, old_str if isinstance(old_str, str) else "", new_str
    return path, None, None


def _checked_lines(text, old_str, new_str):
    """Line numbers in `text` that a `replace` call actually added or changed."""
    if new_str is None:
        return None
    chunk = new_str.strip("\n")
    if not chunk.strip():
        return set()
    offsets = _changed_offsets((old_str or "").strip("\n"), chunk)
    if not offsets:
        return set()
    numbers = set()
    at = text.find(chunk)
    while at >= 0:
        first = text.count("\n", 0, at) + 1
        numbers.update(first + off for off in offsets)
        at = text.find(chunk, at + 1)
    return numbers


def _extract_content(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts)
    return ""


def typed_messages(path):
    """User-typed prompts from a Gemini CLI JSONL or legacy JSON transcript."""
    messages = []
    try:
        with io.open(path, encoding="utf-8", errors="replace") as handle:
            raw = handle.read()
    except (OSError, TypeError):
        return messages

    stripped = raw.lstrip()
    if not stripped:
        return messages

    # Legacy single-JSON session file: {"messages": [{"type": "user", ...}]}
    try:
        doc = json.loads(raw)
    except ValueError:
        doc = None

    if isinstance(doc, dict) and isinstance(doc.get("messages"), list):
        for row in doc["messages"]:
            if isinstance(row, dict) and row.get("type") == "user" and "message" not in row:
                text = _extract_content(row.get("content"))
                if text:
                    messages.append(text)
        return messages

    # Current JSONL session format: one JSON object per line.
    for line in raw.splitlines():
        if '"user"' not in line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict) and row.get("type") == "user" and "message" not in row:
            text = _extract_content(row.get("content"))
            if text:
                messages.append(text)
    return messages


def main(argv):
    _hook_io.utf8_streams()
    event = _hook_io.read_event() or {}
    path, old_str, new_str = _saved_target(event)
    if not path or not _gate_core.in_scope(path) or not os.path.isfile(path):
        sys.stdout.write("{}\n")
        return 0

    profile, _source = _preference.resolve_preference(
        _hook_io.preference_arg(argv, PREFERENCE_PATH)
    )
    if profile not in _preference.ACTIVE:
        sys.stdout.write("{}\n")
        return 0

    hook_dir = os.path.dirname(os.path.abspath(__file__))
    cl = _gate_core._checker(_hook_io.plugin_root(argv, hook_dir))
    with io.open(path, encoding="utf-8", errors="replace") as handle:
        text = handle.read()

    found = cl.scan_text(text, profile)
    mine = _checked_lines(text, old_str, new_str)
    if mine is not None:
        found = [finding for finding in found if finding[0] in mine]
    if not found:
        sys.stdout.write("{}\n")
        return 0

    typed = typed_messages(event.get("transcript_path"))
    report, kept = _gate_core.split_kept(cl, text, found, typed)
    kept_labels = [
        "%s line %d [%s]" % (os.path.basename(path), lineno, name)
        for lineno, name, _ in kept
    ]

    if not report:
        if kept_labels:
            sys.stdout.write(json.dumps({
                "systemMessage": (
                    "grounded-copy kept %d sentence(s) you wrote: %s"
                    % (len(kept_labels), ", ".join(kept_labels))
                )
            }) + "\n")
        else:
            sys.stdout.write("{}\n")
        return 0

    lines = ["grounded-copy gate failed on %s" % path]
    lines += cl.report(path, report)
    if kept_labels:
        lines.append("%d sentence(s) the user wrote stay as written." % len(kept_labels))
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
        sys.stdout.write("{}\n")
        code = 0
    sys.exit(code)
'''

GROUNDED_TOML = r'''description = "Show or change the grounded-copy writing mode (chat, copy, or off)"
prompt = """
Match the user's argument (`{{args}}`) to `chat`, `copy`, or `off`. For an empty or unknown argument, run the status command. Limit the operation to the profile setting.

On Unix or Git Bash, run the selected command:

- `chat`: `sh '${extensionPath}/hooks/run.sh' grounded_tracker.py --set chat`
- `copy`: `sh '${extensionPath}/hooks/run.sh' grounded_tracker.py --set copy`
- `off`: `sh '${extensionPath}/hooks/run.sh' grounded_tracker.py --set off`
- status: `sh '${extensionPath}/hooks/run.sh' grounded_tracker.py --status`

On Windows PowerShell, run the matching launcher:

- `chat`: `& '${extensionPath}\\hooks\\run.cmd' grounded_tracker.py --set chat`
- `copy`: `& '${extensionPath}\\hooks\\run.cmd' grounded_tracker.py --set copy`
- `off`: `& '${extensionPath}\\hooks\\run.cmd' grounded_tracker.py --set off`
- status: `& '${extensionPath}\\hooks\\run.cmd' grounded_tracker.py --status`

Use the selected command as written and keep user-supplied text out of the shell command. For an unknown argument, report the rejected value and the current profile while leaving the saved setting unchanged.

A successful change prints the status and the instructions for the new profile. Apply those instructions from this turn forward.
"""
'''

README = """# grounded-copy for Gemini CLI

Help AI say clearly and get to the point.

This extension gives Gemini CLI the grounded-copy writing rules at session start, a short reminder before each prompt, a check on prose files after the agent saves them, and the `/grounded` command to switch writing modes.

## Install

From a clone of the repository, install or link the extension directory:

    gemini extensions install --path ./dist/gemini/grounded-copy

Or link it in place while tracking local updates:

    gemini extensions link ./dist/gemini/grounded-copy

## Writing mode

Type `/grounded` to see the current mode. Choose `/grounded chat` for everyday interaction and ordinary documents, `/grounded copy` for product pages and marketing copy, or `/grounded off` to turn the rules off. Your choice stays saved after a restart.

The setting lives at `$GEMINI_CLI_HOME/.gemini/grounded-copy/profile`, or `~/.gemini/grounded-copy/profile` by default.

Read the [setup guide](skills/grounded-copy/references/setup.md) for details and the [pattern guide](skills/grounded-copy/references/patterns.md) for examples.

## Package maintenance

This directory is generated by `scripts/build_gemini_adapter.py` in the repository. Edit the source files there, run the builder, and commit the generated files. The builder's `--check` option reports differences, missing files, and unexpected files.

## License

[AGPL-3.0-only](LICENSE). [NOTICE](NOTICE) carries the copyright.
"""


def payloads():
    items = codex._skill_payloads()
    items.append(codex._copy_source("LICENSE", "LICENSE"))
    items.append(codex._copy_source("NOTICE", "NOTICE"))
    for name in ("_hook_io.py", "_policy.py", "_preference.py", "run.sh", "run.cmd"):
        items.append(codex._copy_source("hooks/" + name, "hooks/" + name))
    items.append(codex._copy_source("hooks/grounded_gate.py", "hooks/_gate_core.py"))
    for name in sorted(SEAMS):
        items.append(("hooks/" + name, _gemini_entrypoint(name)))
    items.extend([
        ("hooks/grounded_gate.py", GATE.encode()),
        ("hooks/gemini_activate.cmd", _polyglot_launcher("grounded_activate.py").encode()),
        ("hooks/gemini_tracker.cmd", _polyglot_launcher("grounded_tracker.py").encode()),
        ("hooks/gemini_gate.cmd", _polyglot_launcher("grounded_gate.py").encode()),
        ("hooks/hooks.json", HOOKS.encode()),
        ("commands/grounded.toml", GROUNDED_TOML.encode()),
        ("gemini-extension.json", MANIFEST.encode()),
        ("README.md", README.encode()),
    ])
    return [(os.path.normpath(os.path.join(ADAPTER, dest)), data) for dest, data in items]


if __name__ == "__main__":
    items = payloads()
    if "--check" in sys.argv[1:]:
        sys.exit(codex.check(ADAPTER, items, "gemini"))
    sys.exit(codex.build(ADAPTER, items))
