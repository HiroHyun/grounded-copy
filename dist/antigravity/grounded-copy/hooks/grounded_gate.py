#!/usr/bin/env python3
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
