<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/user-attachments/assets/b879b4bb-88dc-4980-b604-e91f3677cfc4">
    <img src="assets/banner.png" alt="Grounded Copy. The printer isn’t broken, it needs paper, with “isn’t broken, it” struck out. Help AI say clearly and get to the point." width="960">
  </picture>
</p>

<p align="center">
  <strong>Output rules and a copy checker for AI agents.</strong>
</p>

<p align="center">
  <a href="https://github.com/HiroHyun/grounded-copy/actions/workflows/copy-lint.yml"><img src="https://github.com/HiroHyun/grounded-copy/actions/workflows/copy-lint.yml/badge.svg" alt="Self-test status"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-AGPL--3.0--only-2ea44f.svg" alt="AGPL-3.0-only License"></a>
  <a href="https://www.skills.sh/hirohyun/grounded-copy"><img src="https://www.skills.sh/b/hirohyun/grounded-copy" alt="Skills CLI installs"></a>
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.zh.md">简体中文</a>
</p>

<p align="center">
  <a href="#try-it">Try it</a> ·
  <a href="#install">Install</a> ·
  <a href="#choose-a-writing-mode">Choose a writing mode</a> ·
  <a href="#how-it-works">How it works</a> ·
  <a href="#before-and-after">Before and after</a> ·
  <a href="#more-help">More help</a>
</p>

# grounded-copy

`grounded-copy` makes your agent state the fact and get to the point, in chat replies and in the documents it writes. A separate mode covers product pages and marketing copy.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/user-attachments/assets/31ba417f-c204-4217-9ed7-5b0faa5e1cca">
    <img src="https://github.com/user-attachments/assets/0dfe252d-d725-4343-a909-b6b2846f1f35" alt="Grounded Copy helps AI say clearly and get to the point: with the plugin, 14% of answers hold a phrase Grounded Copy targets, such as “rather than”, against 64% without the plugin and 20% for people on the same questions, drawn as a line across the bars; words and tokens per answer stay about the same, 276.3 words and 23,084 tokens with the plugin against 273.8 words and 22,871 tokens without it; the questions are 300 everyday questions from Stack Exchange, answered by gpt-6.1-sol in Codex, and people’s answers are replies posted there." width="880">
  </picture>
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/user-attachments/assets/26b41acc-313e-4621-853e-f81ec13a2027">
    <img src="https://github.com/user-attachments/assets/c658b186-8642-4470-8d22-b5f9f6b20adb" alt="One pass or two, on 100 of the questions: with Grounded Copy, an answer takes 36% fewer tokens and 40% less time than writing it and then rewriting it with humanizer; the lowest figure in each row is marked, and in the rows for tokens, seconds and words every other figure says how much more it is; with no plugin, the agent writes the answer in one request, with 22,441 tokens (lowest), 47.3 seconds (10% more than the lowest) and 280.1 words (lowest) per answer, and 68% of answers hold a phrase Grounded Copy targets and 71% a long dash, a habit humanizer targets; with Grounded Copy, the rules load before the agent writes the answer in one request, with 23,501 tokens (5% more than the lowest), 42.9 seconds (lowest) and 283.8 words (1% more than the lowest), and 18% of answers hold a targeted phrase (lowest) and 37% a long dash; and writing then rewriting with humanizer, an open-source skill whose column counts both passes, takes two requests, with 36,957 tokens (65% more than the lowest), 71.7 seconds (67% more than the lowest) and 287.0 words (2% more than the lowest), and 45% of answers hold a targeted phrase and 1% a long dash (lowest)." width="880">
  </picture>
</p>

## Try it

The Claude Code and Codex plugins load the `chat` rules at the start of every session, with no instruction from you. Start a session and ask your question. In Codex, approve the plugin's hooks the first time the app asks.

With the skill alone, name it in your request, such as "Use grounded-copy to answer."

In a chat app with no plugin support, paste the rules into its custom instructions. [Setup](skills/grounded-copy/references/setup.md#chat-apps) says which part to copy.

For product pages or marketing copy, switch to `copy` mode first.

## Install

The installer needs Python 3 and Node.js with `npx`. It adds the plugin to Claude Code and Codex when it finds them, and installs the skill for other agents through the Skills CLI.

**macOS, Linux, WSL, or Git Bash:**

```bash
curl -fsSL https://raw.githubusercontent.com/HiroHyun/grounded-copy/main/install.sh | sh
```

**Windows PowerShell:**

```powershell
irm https://raw.githubusercontent.com/HiroHyun/grounded-copy/main/install.ps1 | iex
```

<details>
<summary><strong>To install for one agent</strong></summary>

<br>

| Install for | Commands |
|---|---|
| Claude Code | `claude plugin marketplace add HiroHyun/grounded-copy`<br>`claude plugin install grounded-copy@hirohyun-plugins -s user` |
| Codex | `codex plugin marketplace add HiroHyun/grounded-copy`<br>`codex plugin add grounded-copy@hirohyun-plugins` |
| Agents supported by the Skills CLI | `npx skills add HiroHyun/grounded-copy --skill grounded-copy --yes` |

</details>

> [!TIP]
> The plugins apply the rules in every chat, check the files the agent saves, and save your writing mode. A skill on its own loads when the agent judges it relevant.
>
> See [setup](skills/grounded-copy/references/setup.md) for installation checks, updates, Windows help, and removal.

## Choose a writing mode

Your choice stays saved after a restart.

| Mode | Use it for |
|---|---|
| `chat` (default) | Everyday interaction and ordinary document processing. |
| `copy` | Product pages, marketing copy, and similar text. |
| `off` | Work that needs the original wording or a different writing style. |

**Claude Code:**

```text
/grounded-copy:grounded chat
/grounded-copy:grounded copy
/grounded-copy:grounded off
```

Use `/grounded-copy:grounded` to see the current mode.

**Codex:**

```text
$grounded-profile chat
$grounded-profile copy
$grounded-profile off
$grounded-profile status
```

> [!IMPORTANT]
> **For a faithful translation, set `off` first.** The rules can otherwise prompt the agent to remove a comparison that belongs to the original text.

## How it works

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/user-attachments/assets/2494c433-cf05-4cd5-9ab5-a2519345dee3">
    <img src="https://github.com/user-attachments/assets/b2534415-9c40-4831-b293-e7f4c1029531" alt="One rule: state the fact; for each “not”, the agent decides whether to cut it, state the fact behind it, or keep it, shown in three drafts and what the agent writes: when the fact already answers it, the agent cuts the first half, so “The file isn’t missing, it’s empty.” becomes “The file is empty.” (tagged Cut); when a fact sits behind it, the agent says that fact, so “The museum is no longer free on Sundays.” becomes “The museum charges on Sundays.” (tagged Fact stated); and when the warning is the fact, the agent keeps it, so “Do not mix bleach and ammonia.” stays as written (tagged Kept)." width="880">
  </picture>
</p>

- The plugin loads the rules when a session starts, so the agent's first draft follows them.
- When the agent saves a file, the plugin checks what the save added, and the agent rewrites each flagged sentence.
- A sentence you typed yourself stays as you wrote it.

## Before and after

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/user-attachments/assets/a9e9f988-ee3f-4f21-a561-fcb9e88a5a18">
    <img src="https://github.com/user-attachments/assets/21407bae-a4d9-4716-8736-f3b1546b3ab2" alt="One question from the run, “When do children become aware of time?”, asked by user 2221 on Parenting Stack Exchange (https://parenting.stackexchange.com/q/20350, CC BY-SA 3.0): in an excerpt from a 227-word answer without the plugin, the agent writes “These are broad ranges, not deadlines.”, and the checker flags “not deadlines”; in an excerpt from a 209-word answer with Grounded Copy, it writes “These are broad ranges. Research finds that performance depends on the language a child speaks and how the question is asked.”; the sentences around each excerpt show in a lighter colour; and this happened on 151 of the 300 questions, where only the answer without the plugin held such a phrase, while the reverse happened on 2." width="880">
  </picture>
</p>

The [pattern guide](skills/grounded-copy/references/patterns.md) has more examples.

## More help

- [Setup](skills/grounded-copy/references/setup.md): installation checks, checking a file, and troubleshooting.
- [Writing rules](skills/grounded-copy/SKILL.md): the instructions the agent reads.
- [Pattern guide](skills/grounded-copy/references/patterns.md): phrases to review and sample rewrites.
- [Contributing](CONTRIBUTING.md): how to propose changes.
- [License](LICENSE): AGPL-3.0-only. [NOTICE](NOTICE) carries the copyright.
