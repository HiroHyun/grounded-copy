#!/usr/bin/env python3
"""The policy text: what the hooks and `--set` put in front of the model.

Three shapes come out of this module, and skills/grounded-copy/references/setup.md defines each one
under `### Profile lifecycle`:

- the **session policy**, which SessionStart injects
- the **turn reminder**, which UserPromptSubmit injects
- a **governing directive**, which `--set` prints when it records a new
  preference

Every one of them is assembled from SKILL.md at runtime, so a rule edit lands
without a code change. The workflow, the integrity rules, and the three excluded
closures load with the skill itself when a copy task calls for them, and so do
the trigger catalogs and rewrite tables in skills/grounded-copy/references/patterns.md.

Transport stays outside this module: it reads no environment and takes the
plugin root as an argument.
"""

import os
import re

# Where the skill sits under the plugin root. One path covers every shipped
# layout: the Claude plugin, a skills-directory clone, the generated Codex
# tree, and a checkout.
SKILL_RELATIVE = os.path.join("skills", "grounded-copy", "SKILL.md")

# Sections both profiles carry, in payload order.
CORE_HEADINGS = (
    "## The one banned move",
    "## Positive forms",
    "## Scope and precedence",
    "## Sourcing",
    "## Suspended lists",
)

# The section the `copy` profile adds.
MARKETING_HEADING = "## Marketing register"

LOOPHOLE_HEADING = "## Loophole closures"

# The closures the `copy` profile adds, in SKILL.md order. Two others came out
# into the rules that already stated them: the quote closure into
# `## Scope and precedence`, whose verbatim rule covers invented testimonials,
# and the headline closure into `## Marketing register`, which enumerates
# headline and CTA scope. These two carry content no core rule states.
COPY_LABELS = (
    '- **"It\'s a different language."**',
    '- **"The linter passed, so it\'s fine."**',
)

COPY_LEAD = "The copy profile adds these closures from the skill:"

SESSION_HEADER = "GROUNDED PROSE ACTIVE — profile: {profile}"

# The Claude slash command. A copied entrypoint passes its own host's verb
# instead; this module names one host in a default and reads no environment to
# discover another.
CLAUDE_SWITCH = "/grounded-copy:grounded chat|copy|off"

SWITCH_LINE = "Profile: {profile}. Switch: `{switch}`."

# Every clause here holds a boundary the session policy states once and the
# turn reminder keeps in reach. `Prefer established positive terms` came out:
# `## Positive forms` carries it at session start. The fence clause stays
# because a fence is where the observed slips landed, and the rules govern
# inside one.
TURN_REMINDER = (
    "GROUNDED PROSE ({profile}). State what the subject is or does. No "
    "contrast, era-ending, or hype. Rules hold in quotes, fences, and "
    "comments; given source text stays verbatim. A user instruction outranks "
    "this; name the rule."
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

# Extraction sizes measured 2026-09-08 against SKILL.md, after the quoted
# banned forms moved to skills/grounded-copy/references/patterns.md so SKILL.md passes copy_lint.py
# itself. These count the rules body alone; hook stdout adds the header and the
# switch line, 106 bytes. The READMEs publish the same figures under "What each
# mode costs", and `grounded_activate.py --self-test` reports the current ones.
BASELINE_BYTES = 3693
COPY_BASELINE_BYTES = 5118
TURN_BASELINE_BYTES = 218

# (floor, ceiling) per payload. The ceiling bounds growth against the figure the
# documentation published when the range was set: a payload that passes it fails
# the self-test. An exact-size assertion would fail on every intentional rule
# addition and get muted, so the band leaves room for one. The floor catches an
# extraction that returns a stub while every structural assertion still passes.
BYTE_RANGE = (3350, 4300)
COPY_BYTE_RANGE = (4850, 6200)
TURN_BYTE_RANGE = (160, 260)


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


def session_policy(skill_text, profile, switch=None):
    """What SessionStart injects.

    ``switch`` is the host's profile verb. The Claude slash command is the
    default; the Codex entrypoint passes `$grounded-profile` through its seam.
    """
    body = policy_body(extract(skill_text), profile)
    return "\n\n".join((
        SESSION_HEADER.format(profile=profile),
        body,
        SWITCH_LINE.format(profile=profile, switch=switch or CLAUDE_SWITCH),
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
    """Read the skill from the plugin root, with a source-tree fallback.

    Every shipped layout puts the skill at the same relative path under the
    plugin root: a Claude marketplace install, a skills-directory clone, the
    generated Codex tree, and a plain checkout, whose root ``plugin_root()``
    resolves as the hooks directory's parent. The second candidate covers a
    root handed in wrong.
    """
    for candidate in (
        os.path.join(plugin_root, SKILL_RELATIVE),
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", SKILL_RELATIVE
        ),
    ):
        try:
            with open(candidate, encoding="utf-8") as handle:
                return handle.read()
        except OSError:
            continue
    return ""


def self_test(plugin_root):
    """Assert structure and budget, report size.

    An exact-size assertion would fail on every intentional SKILL.md rule
    addition, and a test that fails for correct work gets muted. A budget
    ceiling fails only when a payload passes the figure the documentation
    publishes, which is the growth this gate exists to catch.
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
    turn_size = len(turn_reminder("chat").encode("utf-8"))

    if any(line.startswith(MARKETING_HEADING) for line in chat.splitlines()):
        failures.append("chat body carries the marketing register")
    for name, size, budget in (
        ("chat", chat_size, BYTE_RANGE),
        ("copy", copy_size, COPY_BYTE_RANGE),
        ("turn reminder", turn_size, TURN_BYTE_RANGE),
    ):
        if not budget[0] <= size <= budget[1]:
            failures.append(
                "%s payload of %d bytes sits outside the %d-%d budget"
                % (name, size, budget[0], budget[1])
            )
    if copy_size <= chat_size:
        failures.append("copy policy matches or trails chat policy")

    # The budget is what fails this run; the baseline and its delta report
    # movement since the figures were published. Printing both keeps a nonzero
    # delta readable as news rather than as a failure.
    print(
        "self-test: chat %d bytes, budget %d-%d, baseline %d, delta %+d; "
        "copy %d bytes, budget %d-%d, baseline %d, delta %+d; "
        "turn reminder %d bytes, budget %d-%d, baseline %d, delta %+d"
        % (
            chat_size, BYTE_RANGE[0], BYTE_RANGE[1],
            BASELINE_BYTES, chat_size - BASELINE_BYTES,
            copy_size, COPY_BYTE_RANGE[0], COPY_BYTE_RANGE[1],
            COPY_BASELINE_BYTES, copy_size - COPY_BASELINE_BYTES,
            turn_size, TURN_BYTE_RANGE[0], TURN_BYTE_RANGE[1],
            TURN_BASELINE_BYTES, turn_size - TURN_BASELINE_BYTES,
        )
    )
    for failure in failures:
        print("self-test FAIL: " + failure)
    return 1 if failures else 0
