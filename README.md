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

1. **`SKILL.md`** teaches the agent the banned move and its seven shapes,
   the deletion test that decides every negative clause, and loophole
   closures written against the ways agents rationalize around style
   rules (cross-sentence contrast, translation, "the linter passed").
   `references/patterns.md` carries the complete trigger phrases for each
   shape and a bad → good rewrite for every category.
2. **`scripts/copy_lint.py`** is a zero-dependency Python 3 linter with
   50+ enumerated patterns. Exit code 1 blocks the task; the agent must
   rewrite the copy, and the skill forbids editing the linter.
3. **Session hooks** put the core rules in context at every session start
   and repeat a one-line reminder each turn, which reaches chat replies.
   A skill description scoped to copy tasks leaves those uncovered, since
   the model decides when a skill applies and a chat reply reads as
   ordinary conversation. Both hooks supply guidance; deterministic
   interception of model output waits for layer 4.
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

## Supported agents and installation paths

| Path | Agent | Installs | Needs |
|---|---|---|---|
| [Portable skill](#portable-skill) | any agent the Skills CLI supports | skill, references, linter | Node (for `npx`), Python 3 to run the linter |
| [Claude Code marketplace](#claude-code-marketplace) | Claude Code | skill, hooks, profiles, slash command | Claude Code with `/plugin`, Python 3, `sh` |
| [Skills-directory clone](#skills-directory-clone) | Claude Code | the same, read in place | `git`, Python 3, `sh` |
| [Codex marketplace](#codex-marketplace) | Codex, ChatGPT | skill, references, linter | Codex with `/plugins`, Python 3 |
| [Project checkout](#project-checkout-for-ci-and-other-agents) | CI, Codex, Gemini, humans | files at stable in-repo paths | `git`, Python 3 |
| [Linter only](#linter-only) | any | the gate | Python 3 |

### Portable skill

```bash
npx skills@latest add HiroHyun/grounded-copy
```

The Skills CLI reads the root `SKILL.md`, detects supported agents, and
installs the skill in their configured skill directories.

```bash
npx skills@latest add HiroHyun/grounded-copy --skill grounded-copy --global --yes
npx skills@latest add HiroHyun/grounded-copy --list
npx skills@latest update grounded-copy
npx skills@latest remove grounded-copy
```

`--list` prints the skill metadata without installing. `update` takes
installed skill names and refreshes them from their source; `-g` restricts the
run to global skills and `-p` to project skills. `remove` deletes the installed
copy. The CLI records the files it manages in a `.source` manifest: `SKILL.md`,
`references/patterns.md`, `references/setup.md`, and `scripts/copy_lint.py`.

### Direct skill download

Every file is plain text under MIT, so a checkout is optional:

```bash
curl -L https://github.com/HiroHyun/grounded-copy/archive/refs/heads/main.tar.gz | tar xz
```

Or take the four files the skill needs:

```bash
base=https://raw.githubusercontent.com/HiroHyun/grounded-copy/main
mkdir -p grounded-copy/references grounded-copy/scripts
curl -o grounded-copy/SKILL.md               $base/SKILL.md
curl -o grounded-copy/references/patterns.md $base/references/patterns.md
curl -o grounded-copy/references/setup.md    $base/references/setup.md
curl -o grounded-copy/scripts/copy_lint.py   $base/scripts/copy_lint.py
```

Point any agent at `SKILL.md` and run `copy_lint.py` from the command line.

### Claude Code marketplace

This repository hosts its own marketplace, `hirohyun-plugins`, at
`.claude-plugin/marketplace.json`. Add it, then install the plugin:

```shell
/plugin marketplace add HiroHyun/grounded-copy
/plugin install grounded-copy@hirohyun-plugins
/reload-plugins
```

`/plugin install` opens the plugin details, where you pick user, project, or
local scope. `/reload-plugins` activates it in the current session.

Manage it afterwards:

```shell
/plugin marketplace update hirohyun-plugins
/plugin disable grounded-copy@hirohyun-plugins
/plugin enable grounded-copy@hirohyun-plugins
/plugin uninstall grounded-copy@hirohyun-plugins
/plugin marketplace remove hirohyun-plugins
```

`/plugin marketplace remove` also uninstalls the plugins installed from that
marketplace; `/plugin marketplace update` refreshes the catalog and keeps them.

The same operations run from the shell for scripting:

```bash
claude plugin marketplace add HiroHyun/grounded-copy
claude plugin install grounded-copy@hirohyun-plugins --scope project
claude plugin marketplace list --json
claude plugin uninstall grounded-copy@hirohyun-plugins --scope project
claude plugin marketplace remove hirohyun-plugins
```

The marketplace entry sets `"source": "./"`, so the plugin is this repository.
A relative source resolves against a local copy of the marketplace, which means
adding it from GitHub or a git URL; adding a direct URL to the `marketplace.json`
file downloads only that file and the relative source fails to resolve.

Third-party marketplaces have auto-update disabled by default. Turn it on from
`/plugin` → **Marketplaces** → the marketplace → **Enable auto-update**.

### Skills-directory clone

A clone into a skills directory is read in place, with no plugin cache:

```bash
git clone https://github.com/HiroHyun/grounded-copy ~/.claude/skills/grounded-copy
```

Remove or rename any earlier portable install first; the clone needs an empty
destination. Claude Code loads the folder as `grounded-copy@skills-dir` on the
next session, and both hooks start. `git pull` in that directory updates it.

Roll back with `claude plugin disable grounded-copy@skills-dir`, which leaves
the skill in place, or delete `.claude-plugin/` and restart to return the
folder to a plain skill.

### Codex marketplace

The same repository hosts a Codex marketplace at
`.agents/plugins/marketplace.json`, listing a skills-only adapter built from
the canonical files:

```bash
codex plugin marketplace add HiroHyun/grounded-copy
codex plugin marketplace list
codex plugin marketplace upgrade
codex plugin marketplace remove hirohyun-plugins
```

Then open the plugin browser, install `grounded-copy`, and start a new session
before using the skill:

```bash
codex /plugins
```

In the browser, Space turns an installed plugin on or off, and **Uninstall
plugin** removes it. To keep it installed and off, set `enabled = false` on its
entry in `~/.codex/config.toml` and restart Codex.

The adapter lives at `adapters/codex/grounded-copy` and carries the skill, both
references, the linter, and the two sample corpora. It ships no hooks, so the
session policy, the turn reminder, the three profiles, and the
`/grounded-copy:grounded` command stay Claude Code features.
`scripts/build_codex_adapter.py --check` and `tests/test_codex_adapter.py`
assert that the adapter matches the canonical files byte-for-byte.

### Project checkout, for CI and other agents

Any path above installs for one machine. A project-local checkout supplies
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

Exit 0 = pass, 1 = rewrite and re-run, 2 = usage or IO error. No dependencies
beyond Python 3.

## Portable capabilities and Claude Code capabilities

| Capability | Portable | Claude Code only |
|---|---|---|
| the `SKILL.md` rules | yes | |
| `references/patterns.md` catalog, nine locales | yes | |
| `scripts/copy_lint.py` and both sample corpora | yes | |
| `SessionStart` policy, repeated after each compaction | | yes |
| `UserPromptSubmit` turn reminder | | yes |
| `chat`, `copy`, `off` profiles and the stored preference | | yes |
| `/grounded-copy:grounded` and the governing directive | | yes |

Requirements for the Claude Code paths: Python 3 on PATH as `python` or
`python3`. The manifest calls `sh hooks/run.sh`; on a Windows setup lacking
`sh`, change both commands to `hooks/run.cmd` in
`.claude-plugin/plugin.json`. Both launchers resolve the interpreter once and
run the hook once.

## Profiles and local state

`/grounded-copy:grounded chat|copy|off` is the one path that records a
preference, and a recorded switch prints a governing directive that takes
effect in the same turn. `chat` carries the core rules; `copy` adds the
marketing register and two closures.

```bash
python hooks/grounded_tracker.py --status
python hooks/grounded_tracker.py --set chat
```

`--status` names the profile, whether it came from the preference file or from
the default, and the resolved path. `--set` exits 0 when it records the
preference, 1 when the write fails, and 2 when it rejects the value.

**What gets written.** One file, and only when you select a profile:
`<config-dir>/grounded-copy/profile`, where config-dir is `$CLAUDE_CONFIG_DIR`
when set and `~/.claude` otherwise. It holds one word. Both hooks are
read-only, the linter writes nothing, and the Codex adapter writes nothing.

`### Profile lifecycle` in `references/setup.md` is the one description of how
the profile preference, the session policy, the turn reminder, and the
effective policy relate.

## Measured recurring context cost

UTF-8 bytes of each hook's stdout, measured 2026-07-31 on Claude Code 2.1.220.
`python hooks/grounded_activate.py --self-test` prints the current figures and
fails when a payload passes its published budget.

| Payload | Bytes | Estimated tokens | When it is spent |
|---|---|---|---|
| `chat` session policy | 4,384 | ~1,100 | every session start, and after each compaction |
| `copy` session policy | 5,941 | ~1,485 | every session start, and after each compaction |
| turn reminder | 218 | ~55 | every prompt |
| `chat` governing directive | 4,527 | ~1,130 | every recorded profile switch |
| `copy` governing directive | 6,084 | ~1,520 | every recorded profile switch |
| `SKILL.md` | 9,789 | ~2,450 | when the skill triggers on a copy task |

**Method.** Bytes are the measured unit: the UTF-8 length of what each hook
writes to stdout, printed by `--self-test`. Token figures are estimates at
bytes ÷ 4, and no token count in this repository comes from a tokenizer.

A 60-turn `chat` session with one compaction and one profile switch spends
about 26,375 bytes, down from 41,594 before the payload was cut.
`### Measured recurring cost` in `references/setup.md` records the history and
what moved where.

## Repository layout

```
grounded-copy/
├── SKILL.md                        # Core rules + workflow + integrity rules
├── LICENSE                         # MIT
├── .claude-plugin/
│   ├── plugin.json                 # Registers the two hooks and the skill
│   └── marketplace.json            # The hirohyun-plugins catalog
├── .agents/plugins/marketplace.json  # The Codex catalog
├── hooks/
│   ├── run.sh, run.cmd             # Resolve Python once, run the hook once
│   ├── grounded_activate.py        # SessionStart: session policy into context
│   ├── grounded_tracker.py         # UserPromptSubmit: turn reminder; --set
│   ├── _preference.py              # The stored profile preference; sole writer
│   ├── _policy.py                  # SKILL.md extraction and policy assembly
│   └── _hook_io.py                 # Hook transport: stdin drain, plugin root
├── commands/grounded.md            # /grounded-copy:grounded chat|copy|off
├── references/
│   ├── patterns.md                 # Trigger phrases, bad → good per category
│   └── setup.md                    # Plugin hooks, distribution, Codex, CI
├── scripts/
│   ├── copy_lint.py                # The deterministic gate
│   └── build_codex_adapter.py      # Builds the Codex adapter; --check
├── adapters/codex/grounded-copy/   # Generated; skills-only Codex plugin
├── tests/
│   ├── bad-samples.md              # Must FAIL the linter (self-test)
│   ├── good-samples.md             # Must PASS the linter (self-test)
│   ├── test_hooks.py               # Hook interface suite
│   ├── test_launchers.py           # Launcher dispatch, arguments, exit codes
│   └── test_codex_adapter.py       # Adapter byte identity and scope
├── .github/workflows/copy-lint.yml # Linter corpora, self-test, both suites
├── .gitattributes                  # Line endings per file type
└── CONTRIBUTING.md
```

The example rows and quoted phrases in this README, in `SKILL.md`, in
`references/patterns.md`, and in `tests/bad-samples.md` contain banned patterns
on purpose; the CI self-test lints only the test corpus.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Short version: every new pattern
needs a real-world sighting, a failing line in `tests/bad-samples.md`,
and a factual counterexample check for false positives.

## License

[MIT](LICENSE). Every redistributed package carries the notice: the Codex
adapter ships its own `LICENSE`, and both plugin manifests and both marketplace
entries declare `MIT`. The source stays public at
https://github.com/HiroHyun/grounded-copy, which is what both marketplaces
fetch from.
