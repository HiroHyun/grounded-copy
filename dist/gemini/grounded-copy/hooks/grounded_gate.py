#!/usr/bin/env python3
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
