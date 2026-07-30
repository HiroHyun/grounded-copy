# grounded-copy

[![self-test](https://github.com/HiroHyun/grounded-copy/actions/workflows/copy-lint.yml/badge.svg)](https://github.com/HiroHyun/grounded-copy/actions/workflows/copy-lint.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A style gate for marketing and web copy. It enforces one rule: every
value proposition states what the subject IS or DOES — a feature, a
number, a mechanism. It bans the contrast move ("not just X", "unlike
others", "say goodbye to") in every disguise it wears, plus hype
vocabulary and vague attribution, across nine languages. A deterministic
Python linter backs the rules and blocks the task until the copy complies.

In Claude Code, two hooks carry the same rules into every session, so chat
replies follow them alongside landing pages and locale files.

## Before and after

| Draft | After grounded-copy |
|---|---|
| "This isn't just a task tracker — it's your team's second brain." | "The tracker links every task to its pull request and posts a status digest to Slack each morning." |
| "Say goodbye to hidden fees." | "The listed price is the complete price; the invoice adds nothing." |
| "Experts agree Acme leads the market." | "Acme holds 34% of the segment, per Gartner's 2025 market report." |
| "This is a neighborhood bakery, not a factory." | "The bakery mills its own flour and ferments each loaf for 18 hours before baking." |
| "The delivery wasn't slow — it arrived before the store opened." | "The courier delivered the order at 6:40 a.m., twenty minutes before the store opened." |
| "Our jeans are sewn in one workshop rather than shipped between contractors." | "Every pair is cut, sewn, and finished in one Los Angeles workshop." |

Same information, carried by specifics.

## How it works

Four layers, each catching what the previous one misses:

1. **`SKILL.md`** teaches the agent the banned move and its ten
   disguises, with loophole closures written against the ways agents
   rationalize around style rules (cross-sentence contrast, invented
   testimonials, "the banned string doesn't appear").
2. **`scripts/copy_lint.py`** is a zero-dependency Python 3 linter with
   50+ enumerated patterns. Exit code 1 blocks the task; the agent must
   rewrite the copy, and the skill forbids editing the linter.
3. **Session hooks** (Tier 2) put the core rules in context at every
   session start and repeat a one-line reminder each turn, which reaches
   chat replies. A skill description scoped to copy tasks leaves those
   uncovered, since the model decides when a skill applies and a chat
   reply reads as ordinary conversation.
4. **File hooks and CI** (see `references/setup.md`) run the linter on
   every file write and every pull request, including human ones.

## Nine languages

The linter catches the same moves in English, Chinese, Russian, Spanish,
Arabic, French, German, Japanese, and Korean — 不仅仅是, не просто,
no es solo, ليس مجرد, pas seulement, mehr als nur, 単なる〜ではない,
단순한 ~이 아닙니다 are all "not just". Constructions with common factual
uses (だけでなく, 뿐만 아니라) lint as warnings and go through the
deletion test in `references/patterns.md`. This makes the gate usable on
locale files: a translation that re-introduces contrast fails CI even
when the English source passed.

## Install

Two tiers. Tier 1 installs the skill on any agent that reads a skill
directory. Tier 2 adds hooks that put the rules in every Claude Code session,
including chat replies.

### Tier 1 — the portable skill

```bash
npx skills@latest add HiroHyun/grounded-copy
```

The Skills CLI reads the root `SKILL.md`, detects supported agents, and
installs the skill in their configured skill directories.

For a global installation with confirmation prompts skipped:

```bash
npx skills@latest add HiroHyun/grounded-copy --skill grounded-copy --global --yes
```

To inspect the skill metadata before installation:

```bash
npx skills@latest add HiroHyun/grounded-copy --list
```

To update an installed skill to the latest version:

```bash
npx skills@latest update grounded-copy
```

`update` takes the installed skill names and refreshes them from their
source; `-g` restricts the run to global skills and `-p` to project skills.

The CLI records the files it manages in a `.source` manifest: `SKILL.md`,
`references/patterns.md`, `references/setup.md`, and `scripts/copy_lint.py`.
The skill activates on copywriting, localization, and review tasks, and the
linter runs from the command line on any agent.

### Tier 2 — always-on for Claude Code

```bash
git clone https://github.com/HiroHyun/grounded-copy ~/.claude/skills/grounded-copy
```

Remove or rename any earlier Tier 1 install first; the clone needs an empty
destination. The clone carries `.claude-plugin/plugin.json`, `hooks/`, and
`commands/`, so Claude Code loads the folder as `grounded-copy@skills-dir` on
the next session and two hooks start:

- `SessionStart` puts the banned move, its ten disguises, the repair, and the
  factual-negation test into session context — roughly 780 tokens, repeated
  after each compaction. The rules reach chat replies, where a skill
  description scoped to copy tasks never triggers.
- `UserPromptSubmit` repeats a one-line reminder, roughly 45 tokens per turn,
  which survives compaction and holds against per-turn injections from other
  plugins.

Switch profiles two ways: `/grounded-copy:grounded chat|copy|off`, or plain
words in a prompt ("switch grounded to copy", "grounded prose off"). Both end
in the same script write. The value persists across restarts at
`<config-dir>/grounded-copy/profile`, where config-dir is `$CLAUDE_CONFIG_DIR`
when set and `~/.claude` otherwise.

Requirements: Python 3 on PATH as `python` or `python3`. The manifest calls
`sh hooks/run.sh`; on a Windows setup lacking `sh`, change that to
`hooks/run.cmd` in `.claude-plugin/plugin.json`. Both launchers resolve the
interpreter once and run the hook once.

Roll back with `claude plugin disable grounded-copy@skills-dir`, which leaves
the skill in place, or delete `.claude-plugin/` and restart to return the
folder to a plain skill.

### Project checkout, for CI and other agents

Either tier above installs for one machine. A project-local checkout supplies
stable in-repo paths, which CI, Codex, and Gemini all read:

```bash
git clone https://github.com/HiroHyun/grounded-copy .style/grounded-copy
```

Use the copy-paste blocks in `references/setup.md` to connect the linter to
Claude Code hooks, `AGENTS.md`, `GEMINI.md`, GitHub Actions, and CODEOWNERS.

### Linter only

```bash
python3 scripts/copy_lint.py draft.md locales/en.json
cat draft.md | python3 scripts/copy_lint.py --stdin
```

Exit 0 = pass, 1 = rewrite and re-run. No dependencies beyond Python 3.

## Repository layout

```
grounded-copy/
├── SKILL.md                    # Core rules + workflow + integrity rules
├── .claude-plugin/plugin.json  # Tier 2: registers the two hooks
├── hooks/
│   ├── run.sh, run.cmd         # Resolve Python once, run the hook once
│   ├── grounded_activate.py    # SessionStart: ruleset into session context
│   ├── grounded_tracker.py     # UserPromptSubmit: reminder + profile switch
│   └── _payload.py             # Shared stdin, argv, and flag handling
├── commands/grounded.md        # /grounded-copy:grounded chat|copy|off
├── references/
│   ├── patterns.md             # Full catalog: bad → good per category
│   └── setup.md                # Plugin hooks, Codex, CI, CODEOWNERS
├── scripts/copy_lint.py        # The deterministic gate
└── tests/
    ├── bad-samples.md          # Must FAIL the linter (self-test)
    └── good-samples.md         # Must PASS the linter (self-test)
```

The example rows and quoted phrases in this README and `tests/bad-samples.md` contain banned
patterns on purpose; the CI self-test lints only the test corpus.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Short version: every new pattern
needs a real-world sighting, a failing line in `tests/bad-samples.md`,
and a factual counterexample check for false positives.

## License

[MIT](LICENSE)
