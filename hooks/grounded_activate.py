#!/usr/bin/env python3
"""SessionStart hook: put the grounded prose ruleset in session context.

Stdout becomes session context, so the rules arrive with no skill-trigger
judgment involved. No matcher, so it also fires after every compaction.

Three pieces come from SKILL.md at runtime: the intro with its example pair,
the "## The one banned move" section, and the factual-negation bullet. The
`copy` profile adds four closures that govern marketing register. The
workflow, the integrity rules, and the remaining closures load with the skill
itself when a copy task calls for them.

Usage:
    grounded_activate.py --plugin-root DIR
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

# The closures the `copy` profile adds, in SKILL.md order.
COPY_LABELS = (
    '- **"It\'s in a quote/testimonial."**',
    '- **"It\'s a headline/CTA/meta tag, not body copy."**',
    '- **"It\'s a different language."**',
    '- **"The linter passed, so it\'s fine."**',
)

COPY_LEAD = "The copy profile adds these closures from the skill:"

# Extraction sizes measured 2026-07-31 against SKILL.md.
BASELINE_BYTES = 3027
COPY_BASELINE_BYTES = 4143
BYTE_RANGE = (2400, 3800)
COPY_BYTE_RANGE = (3400, 5200)

SWITCH_LINE = (
    "Profile: {profile}. Switch with `/grounded-copy:grounded chat|copy|off`, "
    "or by typing a whole-prompt instruction (\"switch grounded to copy\", "
    "\"stop grounded prose\"). The `copy` profile adds the marketing-register "
    "closures; `off` stops this block and the per-turn reminder."
)


def _strip_frontmatter(text):
    return re.sub(r"^---.*?---\s*", "", text, flags=re.S)


def _section(lines, start):
    """The lines from a heading up to the next `## ` heading."""
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break
    return "\n".join(lines[start:end]).strip()


def _bullet(section, label):
    """One bold-labelled bullet out of a section, or an empty string."""
    match = re.search(
        re.escape(label) + r".*?(?=\n- \*\*|\n## |\Z)", section, flags=re.S
    )
    return match.group(0).strip() if match else ""


def extract(skill_text):
    """The payload pieces as a dict. Missing pieces come back empty."""
    body = _strip_frontmatter(skill_text)
    lines = body.splitlines()

    banned_start = loophole_start = None
    for i, line in enumerate(lines):
        if banned_start is None and line.startswith(BANNED_HEADING):
            banned_start = i
        elif loophole_start is None and line.startswith(LOOPHOLE_HEADING):
            loophole_start = i

    pieces = {"intro": "", "banned": "", "factual": "", "closures": []}
    if banned_start is None:
        return pieces

    pieces["intro"] = "\n".join(lines[:banned_start]).strip()
    pieces["banned"] = _section(lines, banned_start)

    if loophole_start is not None:
        loophole = _section(lines, loophole_start)
        pieces["factual"] = _bullet(loophole, FACTUAL_LABEL)
        pieces["closures"] = [_bullet(loophole, label) for label in COPY_LABELS]

    return pieces


def payload_body(pieces, profile):
    """The rules for one profile, without the header or the switch line."""
    parts = [pieces["intro"], pieces["banned"], pieces["factual"]]
    if profile == "copy":
        closures = [c for c in pieces["closures"] if c]
        if closures:
            parts.append(COPY_LEAD + "\n\n" + "\n".join(closures))
    return "\n\n".join(p for p in parts if p)


def build(skill_text, profile):
    header = "GROUNDED PROSE ACTIVE — profile: " + profile
    body = payload_body(extract(skill_text), profile)
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
    """Assert structure, report size.

    An exact-size assertion would fail on every intentional SKILL.md rule
    addition, and a test that fails for correct work gets muted.
    """
    skill = read_skill(plugin_root)
    if not skill:
        print("self-test: SKILL.md unreadable")
        return 1

    pieces = extract(skill)
    failures = []
    if not pieces["intro"]:
        failures.append("piece 1 (intro) empty")
    if not pieces["banned"]:
        failures.append("piece 2 (banned move section) empty")
    if not pieces["factual"]:
        failures.append("piece 3 (factual-negation bullet) empty")
    if BANNED_HEADING not in pieces["banned"]:
        failures.append("banned-move heading missing")
    if LOOPHOLE_HEADING not in skill:
        failures.append("loophole heading missing from SKILL.md")
    if FACTUAL_LABEL not in pieces["factual"]:
        failures.append("factual bullet label missing")

    for label, closure in zip(COPY_LABELS, pieces["closures"]):
        if not closure:
            failures.append("copy closure missing: " + label)

    chat = payload_body(pieces, "chat")
    copy = payload_body(pieces, "copy")
    chat_size = len(chat.encode("utf-8"))
    copy_size = len(copy.encode("utf-8"))

    if not BYTE_RANGE[0] <= chat_size <= BYTE_RANGE[1]:
        failures.append(
            "chat extraction of %d bytes sits outside the %d-%d range"
            % (chat_size, BYTE_RANGE[0], BYTE_RANGE[1])
        )
    if not COPY_BYTE_RANGE[0] <= copy_size <= COPY_BYTE_RANGE[1]:
        failures.append(
            "copy extraction of %d bytes sits outside the %d-%d range"
            % (copy_size, COPY_BYTE_RANGE[0], COPY_BYTE_RANGE[1])
        )
    if copy_size <= chat_size:
        failures.append("copy payload matches or trails chat payload")

    print(
        "self-test: chat %d bytes, baseline %d, delta %+d; "
        "copy %d bytes, baseline %d, delta %+d"
        % (
            chat_size, BASELINE_BYTES, chat_size - BASELINE_BYTES,
            copy_size, COPY_BASELINE_BYTES, copy_size - COPY_BASELINE_BYTES,
        )
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

    profile, _source = _payload.resolve_profile()
    if profile == "off":
        return 0

    skill = read_skill(plugin_root)
    if not skill:
        return 0

    sys.stdout.write(build(skill, profile))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception:
        sys.exit(0)
