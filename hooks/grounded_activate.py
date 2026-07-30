#!/usr/bin/env python3
"""SessionStart hook: put the grounded prose ruleset in session context.

Claude Code adds this script's stdout to the session as context, so the rules
arrive with no skill-trigger judgment involved. Registered with no matcher, so
it fires on startup, resume, clear, and compact — the ruleset returns after
every compaction.

The payload is extracted from SKILL.md at runtime, which keeps one source of
truth. Three pieces, in order:

  1. the intro through the bad/good example pair
  2. the whole "## The one banned move" section
  3. the '**"This negation is factual."**' bullet from "## Loophole closures"

Everything else stays out. The other loophole closures, the workflow, the
integrity rules, and the references matter when the skill is doing copy work,
and the full text loads then.

Usage:
    grounded_activate.py --plugin-root DIR --data-dir DIR
    grounded_activate.py --self-test [--plugin-root DIR]
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _payload  # noqa: E402

BANNED_HEADING = "## The one banned move"
LOOPHOLE_HEADING = "## Loophole closures"
FACTUAL_LABEL = '- **"This negation is factual."**'

# Recorded baseline for the extraction, measured 2026-07-30 against SKILL.md.
# The plan records 3,028 from a hand-measurement that carried one extra
# separator byte; this is what the shipped extractor produces.
BASELINE_BYTES = 3027
BYTE_RANGE = (2400, 3800)

SWITCH_LINE = (
    "Profile: {profile}. Switch with `/grounded chat|copy|off`. "
    "The `copy` profile adds the marketing-register rules; `off` stops this "
    "block and the per-turn reminder."
)


def _strip_frontmatter(text):
    return re.sub(r"^---.*?---\s*", "", text, flags=re.S)


def extract(skill_text):
    """The three payload pieces, as a list. Missing pieces come back empty."""
    body = _strip_frontmatter(skill_text)
    lines = body.splitlines()

    banned_start = loophole_start = None
    for i, line in enumerate(lines):
        if banned_start is None and line.startswith(BANNED_HEADING):
            banned_start = i
        elif loophole_start is None and line.startswith(LOOPHOLE_HEADING):
            loophole_start = i

    if banned_start is None:
        return ["", "", ""]

    intro = "\n".join(lines[:banned_start]).strip()

    banned_end = len(lines)
    for i in range(banned_start + 1, len(lines)):
        if lines[i].startswith("## "):
            banned_end = i
            break
    banned = "\n".join(lines[banned_start:banned_end]).strip()

    factual = ""
    if loophole_start is not None:
        rest = "\n".join(lines[loophole_start:])
        match = re.search(
            re.escape(FACTUAL_LABEL) + r".*?(?=\n- \*\*|\n## |\Z)", rest, flags=re.S
        )
        if match:
            factual = match.group(0).strip()

    return [intro, banned, factual]


def build(skill_text, profile):
    pieces = extract(skill_text)
    header = "GROUNDED PROSE ACTIVE — profile: " + profile
    body = "\n\n".join(p for p in pieces if p)
    return header + "\n\n" + body + "\n\n" + SWITCH_LINE.format(profile=profile)


def read_skill(plugin_root):
    for candidate in (
        os.path.join(plugin_root, "SKILL.md"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "SKILL.md"),
    ):
        try:
            with open(candidate, encoding="utf-8") as handle:
                return handle.read()
        except OSError:
            continue
    return ""


def self_test(plugin_root):
    """Structural invariants plus a printed delta against the baseline.

    Asserting an exact size would turn every intentional SKILL.md rule
    addition into a red test, and a test that fails for correct work gets
    muted. So the structure carries the assertions and the size reports.
    """
    skill = read_skill(plugin_root)
    if not skill:
        print("self-test: SKILL.md unreadable")
        return 1

    intro, banned, factual = extract(skill)
    failures = []
    if not intro:
        failures.append("piece 1 (intro) empty")
    if not banned:
        failures.append("piece 2 (banned move section) empty")
    if not factual:
        failures.append("piece 3 (factual-negation bullet) empty")
    if BANNED_HEADING not in banned:
        failures.append("banned-move heading missing")
    if LOOPHOLE_HEADING not in skill:
        failures.append("loophole heading missing from SKILL.md")
    if FACTUAL_LABEL not in factual:
        failures.append("factual bullet label missing")

    payload = build(skill, _payload.DEFAULT)
    size = len(("\n\n".join(p for p in (intro, banned, factual) if p)).encode("utf-8"))
    if not BYTE_RANGE[0] <= size <= BYTE_RANGE[1]:
        failures.append(
            "extraction of %d bytes sits outside the %d-%d range"
            % (size, BYTE_RANGE[0], BYTE_RANGE[1])
        )

    delta = size - BASELINE_BYTES
    print(
        "self-test: extraction %d bytes, baseline %d, delta %+d; "
        "full payload %d bytes"
        % (size, BASELINE_BYTES, delta, len(payload.encode("utf-8")))
    )
    for failure in failures:
        print("self-test FAIL: " + failure)
    return 1 if failures else 0


def main(argv):
    paths = _payload.argv_paths(argv)
    hook_dir = os.path.dirname(os.path.abspath(__file__))
    plugin_root = _payload.resolve_plugin_root(paths["plugin_root"], hook_dir)

    if "--self-test" in argv:
        return self_test(plugin_root)

    _payload.read_payload()  # drain stdin; the event fields go unused here

    data_dir = _payload.resolve_data_dir(paths["data_dir"])
    profile = _payload.read_profile(data_dir)
    first_run = profile == _payload.MISSING
    if first_run:
        profile = _payload.DEFAULT
        _payload.write_profile(data_dir, profile)
    elif profile == _payload.INVALID:
        # An untrusted flag falls back to the default and stays untouched, so a
        # hand-edited file survives for its owner to inspect.
        profile = _payload.DEFAULT

    if profile == "off":
        return 0

    skill = read_skill(plugin_root)
    if not skill:
        return 0

    output = build(skill, profile)
    # The resolved path prints every session, not only on first run: it is the
    # only signal distinguishing a real ${CLAUDE_PLUGIN_DATA} from the
    # fallback, and reading it costs one line.
    output += "\nProfile flag: " + _payload.flag_path(data_dir)
    if first_run:
        output += " (created)"
    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception:
        sys.exit(0)
