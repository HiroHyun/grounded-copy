<p align="center">
  <img src="assets/banner.png" alt="grounded-copy: Every claim states a feature, a number, or a mechanism." width="960">
</p>

<p align="center">
  <strong>A prose style gate for every stretch of text a person reads.</strong>
</p>

<p align="center">
  <a href="https://github.com/HiroHyun/grounded-copy/actions/workflows/copy-lint.yml"><img src="https://github.com/HiroHyun/grounded-copy/actions/workflows/copy-lint.yml/badge.svg" alt="Self-test status"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2ea44f.svg" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/languages-9-22c55e.svg" alt="Nine languages">
  <img src="https://img.shields.io/badge/portable_agents-17%2B-22c55e.svg" alt="17 or more portable agents">
</p>

<p align="center">
  <strong>Read this in other languages:</strong>
  <a href="README.md">English</a> ·
  <a href="README.zh.md">简体中文</a>
</p>

<p align="center">
  <a href="#install">Install</a> ·
  <a href="#what-it-does">What it does</a> ·
  <a href="#before-and-after">Before and after</a> ·
  <a href="#nine-languages">Nine languages</a> ·
  <a href="#documentation">Documentation</a>
</p>

`grounded-copy` covers chat replies, documentation, plans, reports, commit
bodies, pull request descriptions, code comments, and product copy. It requires
every claim to name a feature, number, or mechanism. A Python linter detects
documented contrast patterns, hype vocabulary, and vague attribution.

## Install

One command installs the Claude Code and Codex plugins when their CLIs are
available, then installs the portable skill for 17+ agents through the Skills
CLI.

```bash
# macOS · Linux · WSL · Git Bash
curl -fsSL https://raw.githubusercontent.com/HiroHyun/grounded-copy/main/install.sh | sh
```

```powershell
# Windows · PowerShell
irm https://raw.githubusercontent.com/HiroHyun/grounded-copy/main/install.ps1 | iex
```

The launchers require Python 3 and Node. They print each host command before
running it. A checkout exposes the full flags: `sh install.sh --dry-run`,
`python3 install.py --skills-only`, and `python3 install.py --uninstall`.

### Per-host alternatives

| Host | Command |
|---|---|
| Portable skill, 17+ agents | `npx skills add HiroHyun/grounded-copy --skill grounded-copy --yes` |
| Claude Code plugin | `claude plugin marketplace add HiroHyun/grounded-copy`<br>`claude plugin install grounded-copy@hirohyun-plugins -s user` |
| Codex plugin | `codex plugin marketplace add HiroHyun/grounded-copy`<br>`codex plugin add grounded-copy@hirohyun-plugins` |
| Linter from a checkout | `python3 skills/grounded-copy/scripts/copy_lint.py draft.md` |

The portable command copies the canonical skill directory: `SKILL.md`, both
references, the linter, and both test corpora. The Claude Code and Codex
plugins add lifecycle hooks, three stored profiles, and a profile controller.

| Capability | Portable, 17+ agents | Plugin, Claude Code and Codex |
|---|:---:|:---:|
| Rules, catalog, nine locales, linter, and corpora | yes | yes |
| `SessionStart` policy, repeated after compaction |  | yes |
| `UserPromptSubmit` turn reminder |  | yes |
| `chat`, `copy`, and `off` profiles with a stored preference |  | yes |
| Profile controller and governing directive |  | yes |

Agents evaluate the skill description on each turn. Plugin hooks run on their
registered session events, so Claude Code and Codex receive the stored profile
at session start, after compaction, and on each prompt.

When the universal install and Claude plugin share a machine, Claude Code may
list `grounded-copy@skills-dir` as `Not loaded` because the plugin owns the
active skill name. The plugin supplies the skill and hooks.

The Codex cache also carries the linter. Version 0.5.0 uses this path:

```bash
python3 ~/.codex/plugins/cache/hirohyun-plugins/grounded-copy/0.5.0/skills/grounded-copy/scripts/copy_lint.py draft.md
```

## What it does

- **Rule:** `SKILL.md` defines seven contrast shapes, positive constraint
  terms, sourcing rules, and a concrete rewrite method.
- **Linter:** `copy_lint.py` uses the Python 3 standard library and returns
  exit code 0 for a clean file, 1 for findings, and 2 for usage or I/O errors.
- **Session policy:** Claude Code and Codex plugins inject the selected policy
  at session start and a compact reminder on each prompt.
- **CI gate:** the workflow requires the bad corpus to return 1 and the good
  corpus to return 0 on Ubuntu and Windows.

## Before and after

These source examples intentionally cite three blocked patterns. The catalog
contains a concrete rewrite for every documented shape.

| Blocked draft | Grounded rewrite |
|---|---|
| “More than just a project tracker.” | “Acme tracks tasks, links each one to its pull request, and posts a daily status digest to Slack.” |
| “Say goodbye to hidden fees.” | “The listed price is the complete price; the invoice adds nothing.” |
| “Experts agree Acme leads the market.” | “Acme holds 34% of the segment, per Gartner’s 2025 market report.” |

See the full [pattern catalog](skills/grounded-copy/references/patterns.md).

## Nine languages

The linter covers nine languages at three documented depths.

| Tier | Languages | What the regexes match |
|---|---|---|
| Full | English | 57 rules, with one or more rules for each shape |
| Structural | Chinese, Japanese, Korean | a bounded gap between negation and assertion, plus enumerated triggers |
| Enumerated | Russian, Spanish, Arabic, French, German | trigger lists of 6 to 18 phrases across minimizing, era-ending, transcendence, and rhetorical-bait families |

The target-language trigger lists form a floor. Translators also apply the
rule from the catalog: translate the grounded source and preserve its concrete
facts.

## Documentation

- [Setup and wiring](skills/grounded-copy/references/setup.md) covers install
  layout, profiles, hook lifecycle, context cost, CI, and rollback.
- [Pattern catalog](skills/grounded-copy/references/patterns.md) lists every
  documented trigger family and its rewrites.
- [Contributing](CONTRIBUTING.md) covers patterns, languages, and test corpora.
- [MIT License](LICENSE) covers use and redistribution.
