# grounded-copy

[English](README.md) · [简体中文](README.zh.md)

Writing rules and a copy checker for AI assistants.

You ask an assistant to write a README. It describes your product with broad claims, and you still have to explain what a user can do with it. `grounded-copy` tells the assistant to write about the actual features, steps, and facts. You can also run its Python checker on a saved draft.

Use it when you write product pages, project docs, or everyday replies. Give the assistant the facts you want to include and tell it who will read them.

## Try it

After installation, ask your assistant:

> Use grounded-copy to rewrite this README for someone installing the tool for the first time. Keep the commands and technical facts. Explain what they can do after installation. Run the copy checker on the result.

For a product page, supply the details the copy needs:

> Write a short description of our task tracker. It links tasks to pull requests and posts a summary to Slack each morning. Use grounded-copy.

The assistant uses the writing rules to draft and review the text. The checker reports phrases that match its rules. You review whether the result is accurate and reads naturally.

## Install

The installer needs Python 3 and Node.js with `npx`. It installs plugins for Claude Code and Codex when it finds their CLIs. It also runs the Skills CLI to install the skill for supported assistants.

**macOS, Linux, WSL, or Git Bash:**

```bash
curl -fsSL https://raw.githubusercontent.com/HiroHyun/grounded-copy/main/install.sh | sh
```

**Windows PowerShell:**

```powershell
irm https://raw.githubusercontent.com/HiroHyun/grounded-copy/main/install.ps1 | iex
```

To choose one installation method, use the commands below.

| Install for | Commands |
|---|---|
| Claude Code | `claude plugin marketplace add HiroHyun/grounded-copy`<br>`claude plugin install grounded-copy@hirohyun-plugins -s user` |
| Codex | `codex plugin marketplace add HiroHyun/grounded-copy`<br>`codex plugin add grounded-copy@hirohyun-plugins` |
| Assistants supported by the Skills CLI | `npx skills add HiroHyun/grounded-copy --skill grounded-copy --yes` |

The skill includes the rules, examples, and checker. The Claude Code and Codex plugins also load rules at session start and add a reminder with each prompt. These plugins let you save a writing mode.

See [setup](skills/grounded-copy/references/setup.md) for installation checks, Windows help, and removal commands.

## Choose a writing mode

The plugins call these modes *profiles*. Your choice stays saved after a restart.

| Profile | Use it for |
|---|---|
| `chat` (default) | Everyday replies, documentation, and technical explanations. |
| `copy` | Product pages and marketing text. Adds rules for promotional wording. |
| `off` | Work that needs the original wording or a different writing style. |

**Claude Code:**

```text
/grounded-copy:grounded chat
/grounded-copy:grounded copy
/grounded-copy:grounded off
```

Use `/grounded-copy:grounded` to see the current profile.

**Codex:**

```text
$grounded-profile chat
$grounded-profile copy
$grounded-profile off
$grounded-profile status
```

For a faithful translation, set `off` first. The rules can otherwise prompt the assistant to remove a comparison that belongs to the original text. Your explicit instructions take priority over the skill.

## Check a file

From a clone of this repository, run:

```bash
python3 skills/grounded-copy/scripts/copy_lint.py draft.md
```

Use `python` if that is your Python 3 command. You can pass several file paths in one call. The checker uses the Python standard library.

Each finding gives a line number, a rule name, and the matched text. Revise the sentence using the facts in your source, then run the command again.

| Exit code | Meaning |
|---|---|
| `0` | The checker found no matches. |
| `1` | The file contains wording to review. |
| `2` | The command arguments or a file could not be read correctly. |

For a Codex plugin installation, the checker is also in the plugin cache:

```bash
python3 ~/.codex/plugins/cache/hirohyun-plugins/grounded-copy/<version>/skills/grounded-copy/scripts/copy_lint.py draft.md
```

Use the version shown by `codex plugin list` in place of `<version>`.

## Before and after

These are made-up examples. Use facts you can verify in your own copy. The first column deliberately contains phrases the checker reports.

| Draft | Rewrite |
|---|---|
| "More than just a project tracker." | "The tracker links tasks to pull requests and posts a summary to Slack each morning." |
| "Acme is a partner, not a vendor." | "Your account manager joins your planning meeting each quarter." |
| "Acme covers every channel — email, live chat, phone, and the help centre — with one queue." | "Acme puts email, live chat, phone, and help centre requests in one queue." |

The [pattern guide](skills/grounded-copy/references/patterns.md) has more examples.

## What to expect

The plugin gives the assistant instructions. It does not scan or block each chat reply. Run the checker on saved files when you need a repeatable check.

A passing result means the text matched none of the checker's patterns. It does not verify facts or guarantee natural writing. Some ordinary phrases also match the rules. Review the meaning before you change them; use `off` when the task requires wording that the style rules would reject.

The checker covers English, Chinese, Japanese, Korean, Russian, Spanish, Arabic, French, and German. English has the most detailed rules. Chinese, Japanese, and Korean checks include sentence patterns. The other languages use phrase lists. Most checks run one line at a time, so a phrase split over two lines can be missed. The check for lists between paired dashes also works across lines in a paragraph.

## More help

- [Setup](skills/grounded-copy/references/setup.md): profiles, troubleshooting, and project checks.
- [Writing rules](skills/grounded-copy/SKILL.md): the instructions the assistant reads.
- [Pattern guide](skills/grounded-copy/references/patterns.md): phrases to review and sample rewrites.
- [Contributing](CONTRIBUTING.md): how to propose changes.
- [MIT license](LICENSE).
