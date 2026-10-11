#!/usr/bin/env python3
"""PostToolUse hook: check what the agent just saved.

Both plugins register it. It runs copy_lint.py on the saved file under the
saved profile and hands the findings back to the agent on stderr with exit
code 2, which is the one place a grounded-copy hook blocks on purpose.

Text that was already in the file is left alone. An edit is checked on the
lines its replacement text landed on, a Codex patch on the lines it added, and
a whole-file write on every line.

One script serves Claude Code and Codex and tells them apart by the shape of
the event and of the transcript rows. Claude Code names the saved file; Codex
passes the patch it applied.

A sentence the user typed passes. The host names the session transcript in the
event, and the hook reads the user's messages from it. A flagged sentence is
kept when it equals a unit of one of those messages: a sentence, a span in
quotation marks, the text after a colon, or a list item. The standalone checker
has no such option, since an agent that could name its own source text could
grant itself a pass.

Everything else fails toward a report: an unreadable transcript, a row with no
mark of a typed prompt, or a snippet with no single place in the file gives no
pass. An error inside the hook exits 0, like the other two hooks.

Usage:
    grounded_gate.py [--plugin-root DIR] [--preference-path FILE] < event.json
"""

import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _hook_io  # noqa: E402
import _preference  # noqa: E402

# Adapter seam: a copied entrypoint sets this for its host.
PREFERENCE_PATH = None

EXIT_OK = 0
EXIT_FINDINGS = 2

# The checker's own sample files report by design.
FIXTURES = "/skills/grounded-copy/tests/"
# A pasted block arrives inside the typed prompt, wrapped in these tags.
_PASTE_TAG = re.compile(r"</?pasted_content\b[^>]*>")
_QUOTED = re.compile(r'"([^"\n]{3,})"')
# What a sentence may end with, dropped before two sentences are compared.
_TAIL = " \t\"')]*_.!?。！？"
# Codex passes the patch it applied. These headers name the files it wrote.
_PATCH_FILE = re.compile(r"^\*\*\* (?:Add File|Update File|Move to): (.+)$", re.M)
CODEX_TYPED_KINDS = {"user.text", "user.image"}
# The Codex app sends an approved plan as a user message that opens this way.
# The plan's text is the agent's, so the row earns no pass.
CODEX_PLAN = "PLEASE IMPLEMENT THIS PLAN:"


def _preference_path(argv):
    if "--preference-path" in argv:
        index = argv.index("--preference-path")
        if index + 1 < len(argv):
            return argv[index + 1]
    return PREFERENCE_PATH


def _checker(root):
    """Import copy_lint from the skill under the plugin root."""
    # A .pyc beside the checker would ship with the skill.
    sys.dont_write_bytecode = True
    sys.path.insert(0, os.path.join(root, "skills", "grounded-copy", "scripts"))
    import copy_lint
    return copy_lint


def in_scope(path):
    """Prose files: .md, .txt, and anything under a locale folder."""
    norm = path.replace("\\", "/").lower()
    if FIXTURES in norm:
        return False
    return norm.endswith((".md", ".txt")) or bool(re.search(r"/locales?/", norm))


def saved_files(event):
    """(path, what the call wrote there) for each file a tool call wrote.

    Claude Code names one file in tool_input.file_path. An edit carries its
    replacement text, and a whole-file write carries none, which reads as None
    here: every line is the agent's. Codex passes the text of the patch in
    tool_input.command, with one header per file, paths relative to cwd, and a
    `+` before each line it adds.
    """
    tool_input = event.get("tool_input") or {}
    path = tool_input.get("file_path")
    if isinstance(path, str):
        edits = [tool_input] + [
            edit for edit in tool_input.get("edits") or []
            if isinstance(edit, dict)]
        chunks = [edit["new_string"] for edit in edits
                  if isinstance(edit.get("new_string"), str)]
        return [(path, chunks or None)]
    patch = tool_input.get("command")
    if event.get("tool_name") != "apply_patch" or not isinstance(patch, str):
        return []
    # A patch that failed wrote nothing, so its files hold no new prose.
    response = event.get("tool_response")
    if (isinstance(response, str) and response.startswith("Exit code:")
            and not response.startswith("Exit code: 0")):
        return []
    cwd = event.get("cwd") or ""
    added, name = {}, None
    for line in patch.splitlines():
        header = _PATCH_FILE.match(line)
        if header:
            name = header.group(1).strip()
            added.setdefault(name, set())
        elif name and line.startswith("+"):
            added[name].add(line[1:])
    return [(os.path.join(cwd, name), lines) for name, lines in added.items()]


def written_lines(text, wrote):
    """The numbers of the lines a save wrote in `text`, or None for all.

    `wrote` is None, the replacement strings of an edit, or the set of lines
    a patch added. A replacement can start and end inside a line, so it is
    found as a span; a patch adds whole lines.
    """
    if wrote is None:
        return None
    if isinstance(wrote, set):
        return {number for number, line in enumerate(text.splitlines(), 1)
                if line in wrote}
    numbers = set()
    for chunk in wrote:
        chunk = chunk.strip("\n")
        at = text.find(chunk) if chunk.strip() else -1
        while at >= 0:
            first = text.count("\n", 0, at) + 1
            numbers.update(range(first, first + chunk.count("\n") + 1))
            at = text.find(chunk, at + 1)
    return numbers


def _claude_text(row):
    """The text of a prompt the user typed in Claude Code, or ''.

    The transcript schema is undocumented; these marks come from the files.
    A typed prompt carries origin.kind "human". Skill text, subagent prompts,
    and compaction summaries carry a flag, and command echoes carry no origin.
    Tool results sit in user rows too and are left out here.
    """
    if row.get("type") != "user":
        return ""
    if (row.get("origin") or {}).get("kind") != "human":
        return ""
    if row.get("isMeta") or row.get("isSidechain") or row.get("isCompactSummary"):
        return ""
    content = (row.get("message") or {}).get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            block.get("text", "") for block in content
            if isinstance(block, dict) and block.get("type") == "text")
    return ""


def _codex_text(row):
    """The text of a prompt the user typed in Codex, or ''.

    A rollout row marks each content item with a kind. A typed prompt holds
    typed text and images alone. Instruction files, environment notes, and app
    pages carry other kinds, and a row with no kinds is left out. The rollout
    format is undocumented too; these marks come from rollout files.
    """
    payload = row.get("payload") or {}
    if (row.get("type") != "response_item" or payload.get("type") != "message"
            or payload.get("role") != "user"):
        return ""
    kinds = (payload.get("internal_chat_message_metadata_passthrough")
             or {}).get("content_item_kinds")
    if not kinds or set(kinds) - CODEX_TYPED_KINDS:
        return ""
    text = "\n".join(
        block.get("text", "") for block in payload.get("content") or []
        if isinstance(block, dict) and block.get("type") == "input_text")
    return "" if text.lstrip().startswith(CODEX_PLAN) else text


def typed_messages(path):
    """What the user typed this session, one string per message."""
    messages = []
    try:
        with io.open(path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                # Most rows are assistant turns and tool output.
                if '"human"' not in line and '"user.text"' not in line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(row, dict):
                    continue
                text = _claude_text(row) or _codex_text(row)
                if text:
                    messages.append(text)
    except (OSError, TypeError):
        pass
    return messages


def _fold(cl, text):
    """A sentence as two writers would both produce it: the checker's folding,
    single spaces, no leading marker, no closing punctuation."""
    text = " ".join(cl.normalize(text).split())
    return text.lstrip(cl.LEAD_STRIP).rstrip(_TAIL)


def units(cl, message):
    """The pieces of a message a writer can lift whole.

    Its sentences, each span in quotation marks, the text after a colon, and
    each list item. A paragraph is read joined across its line wraps and line
    by line, so a wrapped sentence and a list item both come out.
    """
    lines = _PASTE_TAG.sub(" ", message).splitlines()
    texts = [joined for joined, _, _, _ in cl.iter_blocks(lines)]
    texts += [cl.normalize(line) for line in lines]
    pieces = []
    for text in texts:
        spans = _QUOTED.findall(text)
        for part in [text] + spans:
            for sentence in cl.SENTENCE_SPLIT.split(part):
                pieces.append(sentence)
                if ": " in sentence:
                    pieces.append(sentence.split(": ", 1)[1])
        pieces += spans
    return {_fold(cl, piece) for piece in pieces} - {""}


def _sentences(cl, text, at, end):
    """The sentences of `text` that the span [at, end) touches."""
    bounds, start = [], 0
    for sep in cl.SENTENCE_SPLIT.finditer(text):
        bounds.append((start, sep.start()))
        start = sep.end()
    bounds.append((start, len(text)))
    return [text[a:b] for a, b in bounds if a < end and at < b]


def _places(text, snippet, low, high):
    """Where `snippet` starts in text[low:high]."""
    found, at = [], text.find(snippet, low)
    while 0 <= at < high:
        found.append(at)
        at = text.find(snippet, at + 1)
    return found


def touched(cl, lines, lineno, snippet):
    """Readings of the sentence a finding sits in, most context first.

    The paragraph joined across wraps, then the line alone, which is how a
    list item reads. A snippet with no single place gives no reading.
    """
    readings = []
    for joined, offsets, _, _ in cl.iter_blocks(lines):
        starts = [start for start, number in offsets if number == lineno]
        if starts:
            later = [start for start, _ in offsets if start > starts[0]]
            places = _places(joined, snippet, starts[0],
                             later[0] if later else len(joined) + 1)
            if len(places) == 1:
                readings.append(_sentences(
                    cl, joined, places[0], places[0] + len(snippet)))
            break
    line = cl.normalize(lines[lineno - 1])
    places = _places(line, snippet, 0, len(line) + 1)
    if len(places) == 1:
        readings.append(_sentences(cl, line, places[0], places[0] + len(snippet)))
    return readings


def split_kept(cl, text, found, typed):
    """(findings to report, findings in sentences the user typed)."""
    if not typed:
        return found, []
    known = set()
    for message in typed:
        known |= units(cl, message)
    lines = text.splitlines()
    report, kept = [], []
    for finding in found:
        lineno, _, snippet = finding
        user_wrote = any(
            sentences and all(_fold(cl, s) in known for s in sentences)
            for sentences in touched(cl, lines, lineno, snippet))
        (kept if user_wrote else report).append(finding)
    return report, kept


def main(argv):
    _hook_io.utf8_streams()
    event = _hook_io.read_event() or {}
    files = [(path, wrote) for path, wrote in saved_files(event)
             if in_scope(path) and os.path.isfile(path)]
    if not files:
        return EXIT_OK

    profile, _source = _preference.resolve_preference(_preference_path(argv))
    if profile not in _preference.ACTIVE:
        return EXIT_OK

    hook_dir = os.path.dirname(os.path.abspath(__file__))
    cl = _checker(_hook_io.plugin_root(argv, hook_dir))
    typed = None
    lines, kept = [], []
    for path, wrote in files:
        with io.open(path, encoding="utf-8", errors="replace") as handle:
            text = handle.read()
        found = cl.scan_text(text, profile)
        mine = written_lines(text, wrote)
        if mine is not None:
            found = [finding for finding in found if finding[0] in mine]
        if not found:
            continue
        if typed is None:
            typed = typed_messages(event.get("transcript_path"))
        report, mine = split_kept(cl, text, found, typed)
        kept += ["%s line %d [%s]" % (os.path.basename(path), lineno, name)
                 for lineno, name, _ in mine]
        if report:
            lines.append("grounded-copy gate failed on %s" % path)
            lines += cl.report(path, report)

    if not lines:
        if kept:
            # Kept sentences only: the user hears about it, the agent does not.
            sys.stdout.write(json.dumps({"systemMessage": (
                "grounded-copy kept %d sentence(s) you wrote: %s"
                % (len(kept), ", ".join(kept)))}))
        return EXIT_OK

    if kept:
        lines.append("%d sentence(s) the user wrote stay as written." % len(kept))
    lines.append("Rewrite each flagged sentence, then save again. "
                 "Do not edit the linter.")
    sys.stderr.write("\n".join(lines) + "\n")
    return EXIT_FINDINGS


if __name__ == "__main__":
    try:
        code = main(sys.argv[1:])
    except Exception:
        # A check that cannot run stays out of the way, as the other hooks do.
        code = EXIT_OK
    sys.exit(code)
