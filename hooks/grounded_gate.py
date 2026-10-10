#!/usr/bin/env python3
"""PostToolUse hook: check the file the agent just saved.

Optional. The plugin manifest registers nothing for it;
skills/grounded-copy/references/setup.md shows the entry a user adds. It runs
copy_lint.py on the saved file under the saved profile and hands the findings
back to the agent on stderr with exit code 2, which is the one place a
grounded-copy hook blocks on purpose.

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


def typed_messages(path):
    """What the user typed this session, one string per message."""
    messages = []
    try:
        with io.open(path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                # Most rows are assistant turns and tool output.
                if '"human"' not in line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                text = _claude_text(row) if isinstance(row, dict) else ""
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
    path = (event.get("tool_input") or {}).get("file_path")
    if not isinstance(path, str) or not in_scope(path) or not os.path.isfile(path):
        return EXIT_OK

    profile, _source = _preference.resolve_preference(_preference_path(argv))
    if profile not in _preference.ACTIVE:
        return EXIT_OK

    hook_dir = os.path.dirname(os.path.abspath(__file__))
    cl = _checker(_hook_io.plugin_root(argv, hook_dir))
    with io.open(path, encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    found = cl.scan_text(text, profile)
    if not found:
        return EXIT_OK

    report, kept = split_kept(
        cl, text, found, typed_messages(event.get("transcript_path")))
    if not report:
        # Kept sentences only: the user hears about it, the agent does not.
        places = ", ".join("line %d [%s]" % (lineno, name)
                           for lineno, name, _ in kept)
        sys.stdout.write(json.dumps({"systemMessage": (
            "grounded-copy kept %d sentence(s) you wrote in %s: %s"
            % (len(kept), os.path.basename(path), places))}))
        return EXIT_OK

    lines = ["grounded-copy gate failed on %s" % path] + cl.report(path, report)
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
