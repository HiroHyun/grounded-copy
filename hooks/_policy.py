#!/usr/bin/env python3
"""The policy text: what the hooks and `--set` put in front of the model.

Three shapes come out of this module, and references/setup.md defines each one
under `### Profile lifecycle`:

- the **session policy**, which SessionStart injects
- the **turn reminder**, which UserPromptSubmit injects
- a **governing directive**, which `--set` prints when it records a new
  preference

Every one of them is assembled from SKILL.md at runtime, so a rule edit lands
without a code change. The workflow, the integrity rules, and the three
excluded closures load with the skill itself when a copy task calls for them.

Transport stays outside this module: it reads no environment and takes the
plugin root as an argument.
"""

import os
import re

# Sections both profiles carry, in payload order.
CORE_HEADINGS = (
    "## The one banned move",
    "## The deletion test",
    "## Positive forms",
    "## Scope and precedence",
    "## Sourcing",
)

# The section the `copy` profile adds.
MARKETING_HEADING = "## Marketing register"

LOOPHOLE_HEADING = "## Loophole closures"

# The closures the `copy` profile adds, in SKILL.md order.
COPY_LABELS = (
    '- **"It\'s in a quote/testimonial."**',
    '- **"It\'s a headline/CTA/meta tag, not body copy."**',
    '- **"It\'s a different language."**',
    '- **"The linter passed, so it\'s fine."**',
)

COPY_LEAD = "The copy profile adds these closures from the skill:"

SESSION_HEADER = "GROUNDED PROSE ACTIVE — profile: {profile}"

SWITCH_LINE = (
    "Profile: {profile}. Switch with `/grounded-copy:grounded chat|copy|off`, "
    "which is the one path that records a preference. The `copy` profile adds "
    "the marketing register and its four closures; `off` stops the session "
    "policy and the turn reminder."
)

TURN_REMINDER = (
    "GROUNDED PROSE ACTIVE ({profile}). State what the subject is or does. "
    "No negation-contrast, no era-ending, no competitor contrast, no hype "
    "register. Rules hold inside quotes, fences, and comments. Source material "
    "you were given stays verbatim. Prefer established positive terms. A direct "
    "user instruction outranks this; name the rule it conflicts with in one "
    "sentence."
)

DIRECTIVE_HEADER = "GROUNDED PROSE — governing profile: {profile} ({source})"

DIRECTIVE_LEAD = (
    "This directive supersedes every grounded-copy policy statement earlier in "
    "this transcript. Those statements stay in the transcript as a record; the "
    "rules below are what governs from this turn onward."
)

DIRECTIVE_LEAD_OFF = (
    "This directive supersedes every grounded-copy policy statement earlier in "
    "this transcript. Those statements stay in the transcript as a record. No "
    "grounded-copy rule governs from this turn onward."
)

DIRECTIVE_LEAD_EMPTY = (
    "The preference is recorded. SKILL.md was unreadable on this run, so the "
    "rules for this profile arrive at the next session start."
)

# Extraction sizes measured 2026-07-31 against SKILL.md. The core grew from
# 3,027 bytes when scope, precedence, the deletion test, positive forms, and
# sourcing moved into it; references/setup.md records the per-session cost.
BASELINE_BYTES = 6333
COPY_BASELINE_BYTES = 8590
BYTE_RANGE = (5000, 8000)
COPY_BYTE_RANGE = (6800, 10800)


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


def _find(lines, heading):
    for i, line in enumerate(lines):
        if line.startswith(heading):
            return i
    return None


def _bullet(section, label):
    """One bold-labelled bullet out of a section, or an empty string."""
    match = re.search(
        re.escape(label) + r".*?(?=\n- \*\*|\n## |\Z)", section, flags=re.S
    )
    return match.group(0).strip() if match else ""


def extract(skill_text):
    """The policy pieces as a dict. Missing pieces come back empty."""
    body = _strip_frontmatter(skill_text)
    lines = body.splitlines()

    pieces = {"intro": "", "core": [], "marketing": "", "closures": []}

    first = None
    for i, line in enumerate(lines):
        if line.startswith("## "):
            first = i
            break
    if first is None:
        return pieces

    pieces["intro"] = "\n".join(lines[:first]).strip()

    for heading in CORE_HEADINGS:
        start = _find(lines, heading)
        pieces["core"].append(_section(lines, start) if start is not None else "")

    start = _find(lines, MARKETING_HEADING)
    if start is not None:
        pieces["marketing"] = _section(lines, start)

    start = _find(lines, LOOPHOLE_HEADING)
    if start is not None:
        loophole = _section(lines, start)
        pieces["closures"] = [_bullet(loophole, label) for label in COPY_LABELS]

    return pieces


def policy_body(pieces, profile):
    """The rules for one profile, without a header or a switch line."""
    parts = [pieces["intro"]] + list(pieces["core"])
    if profile == "copy":
        parts.append(pieces["marketing"])
        closures = [c for c in pieces["closures"] if c]
        if closures:
            parts.append(COPY_LEAD + "\n\n" + "\n".join(closures))
    return "\n\n".join(p for p in parts if p)


def session_policy(skill_text, profile):
    """What SessionStart injects."""
    body = policy_body(extract(skill_text), profile)
    return "\n\n".join((
        SESSION_HEADER.format(profile=profile),
        body,
        SWITCH_LINE.format(profile=profile),
    ))


def turn_reminder(profile):
    """What UserPromptSubmit injects."""
    return TURN_REMINDER.format(profile=profile)


def governing_directive(skill_text, profile, source):
    """What `--set` prints when it records a new preference.

    Self-contained: it restates the whole policy for the new profile, so every
    transition takes one code path with no ordering assumptions. It supersedes
    the earlier text and claims no erasure — a transcript is append-only.
    """
    header = DIRECTIVE_HEADER.format(profile=profile, source=source)
    if profile == "off":
        return header + "\n\n" + DIRECTIVE_LEAD_OFF
    body = policy_body(extract(skill_text), profile)
    if not body:
        return header + "\n\n" + DIRECTIVE_LEAD_EMPTY
    return "\n\n".join((header, DIRECTIVE_LEAD, body))


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
        failures.append("intro empty")
    for heading, section in zip(CORE_HEADINGS, pieces["core"]):
        if not section:
            failures.append("core section empty: " + heading)
        elif not section.startswith(heading):
            failures.append("core section mismatched: " + heading)
    if not pieces["marketing"]:
        failures.append("marketing register empty")
    for label, closure in zip(COPY_LABELS, pieces["closures"]):
        if not closure:
            failures.append("copy closure missing: " + label)

    chat = policy_body(pieces, "chat")
    copy = policy_body(pieces, "copy")
    chat_size = len(chat.encode("utf-8"))
    copy_size = len(copy.encode("utf-8"))

    if any(line.startswith(MARKETING_HEADING) for line in chat.splitlines()):
        failures.append("chat body carries the marketing register")
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
        failures.append("copy policy matches or trails chat policy")

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
