# Setup

Start with the installation commands in the [English README](https://github.com/HiroHyun/grounded-copy#readme) or [中文说明](https://github.com/HiroHyun/grounded-copy/blob/main/README.zh.md). This guide explains how to check an installation, change profiles, and run the checker in a project.

## Check your installation

In Claude Code, run `/grounded-copy:grounded`. In Codex, run `$grounded-profile status`. The result shows the active profile and where the setting is saved.

The default is `chat`. Try asking the agent to rewrite a short paragraph using grounded-copy. To check a saved file, use the `copy_lint.py` command in the README.

The Skills CLI installation includes the writing rules, examples, checker, and sample files. Saved profiles and automatic session reminders come with the Claude Code and Codex plugins.

### After an update

Claude Code loads the plugin from the repository-root package. Codex uses the generated adapter. Skills CLI and manual installations use the canonical skill directory. Each channel carries the same writing guidance and references.

Update through the tool that manages your installation. For a manually copied skill, replace the complete skill directory so its references stay in sync. After updating a plugin, reload it and start a new session to load the revised policy. Check the installed version through the host's plugin list; a source checkout can contain changes awaiting publication.

For English and other languages, read [Paragraph review](patterns.md#paragraph-review). Chinese writing also uses [Chinese paragraph review](patterns.md#chinese-paragraph-review). The examples show how to select useful detail and reduce repeated enumeration. This requires contextual review by the agent; `copy_lint.py` retains its existing pattern checks.

The shared policy selects facts relevant to the task and allows incidental details to be omitted. Exact reproduction applies to verbatim quotations. Explicit requests for complete coverage still govern the result. Reload the updated plugin and start a fresh session so earlier preservation instructions leave the active context.

## Install from a clone

The launchers need Python 3. The Skills CLI also needs Node.js and `npx`.

From the repository root, preview the install commands:

```bash
python3 install.py --dry-run
```

Install the skill through the Skills CLI:

```bash
python3 install.py --skills-only
```

Run `python3 install.py --help` to see all options. The installer prints each host command before running it.

## Profile lifecycle

A profile is a saved writing mode. Use `chat` for everyday writing, `copy` for promotional text, and `off` for work that needs another style. Switch to `off` before translating source text whose wording and comparisons must be preserved.

| Action | Claude Code | Codex |
|---|---|---|
| Everyday writing | `/grounded-copy:grounded chat` | `$grounded-profile chat` |
| Product and marketing copy | `/grounded-copy:grounded copy` | `$grounded-profile copy` |
| Turn the rules off | `/grounded-copy:grounded off` | `$grounded-profile off` |
| Show the saved setting | `/grounded-copy:grounded` | `$grounded-profile status` |

The setting stays saved across restarts. Each host uses its own file:

| Host | Setting file |
|---|---|
| Claude Code | `$CLAUDE_CONFIG_DIR/grounded-copy/profile`, or `~/.claude/grounded-copy/profile` by default |
| Codex | `$CODEX_HOME/grounded-copy/profile`, or `~/.codex/grounded-copy/profile` by default |

The plugin reads this file at session start and after context compaction. It adds the selected writing rules to the agent's context. Each prompt also gets a short reminder of the profile.

A successful switch saves the setting and prints the instructions that apply from that point forward. Earlier instructions remain visible in the conversation. The new instructions tell the agent which profile to follow now.

Use the profile command to change modes during a session. A manual edit of the setting file changes the next reminder, but the full rules load at the next session start.

### Enforcement boundary

The two lifecycle hooks provide instructions to the agent. They do not inspect or block the agent's output. A chat reply reaches you without an automatic copy scan. Run `copy_lint.py` on files you want to check, add it to your project's CI, or turn on the optional hook under [Check files as the agent saves them](#check-files-as-the-agent-saves-them).

The `off` profile stops the session rules and turn reminder. It leaves the checker available as a separate command. Your explicit instructions always take priority over the skill.

### Reading and restoring the preference

For troubleshooting Claude Code from a repository clone:

```bash
python3 hooks/grounded_tracker.py --status
python3 hooks/grounded_tracker.py --set chat
```

These commands use the Claude Code setting path. Use `$grounded-profile` in Codex to change the Codex setting.

A missing, unreadable, oversized, or invalid setting file resolves to `chat`. An older saved value of `technical` also resolves to `chat`. Reading a setting leaves the file unchanged.

A direct `--set` accepts `chat`, `copy`, or `off`, ignoring case and surrounding whitespace. It returns `0` after saving, `1` if saving fails, and `2` for an invalid value. `--status` returns `0`.

The Claude slash command handles an unknown argument by showing status and reporting the rejected value. It keeps the current setting.

## Troubleshooting

### The plugin is installed, but reminders are missing

Check the active profile first. The `off` profile produces empty hook output. Check that the host has enabled the plugin's hooks and approved them where required. Reload the plugin or start a new session after changing hook files.

Both launchers look for `python` and then `python3`, using the first command that reports Python 3. If neither is available, the lifecycle hook exits quietly. Install Python 3 and make its command available to the host.

### Claude Code hooks on Windows

Claude Code runs plugin hooks in Git Bash when it finds one and in PowerShell otherwise. Each hook command dot-sources a launcher in `hooks/`, `claude_activate.cmd` or `claude_tracker.cmd`, that both shells start. Git Bash reads the file as a shell script and runs `run.sh`. PowerShell runs it as a batch file, which hands over to `run.cmd`. The hooks work in either shell without edits to the manifest.

If an earlier version of this guide led you to edit the hook commands in your installed manifest, reinstall or update the plugin to restore the shipped commands.

If an error shows a literal `${CLAUDE_PLUGIN_ROOT}` or `${PLUGIN_ROOT}`, the host did not substitute the plugin path. Check the plugin configuration before running the command again.

### Claude Code shows a duplicate skill

When both the Skills CLI copy and the plugin are installed, Claude Code may show `grounded-copy@skills-dir` as `Not loaded`. The active plugin supplies the skill and hooks. Check the plugin's status before reinstalling.

### The checker reports a sentence you need to keep

The checker matches text patterns. Some phrases also have ordinary factual uses. Read the sentence in context and preserve its meaning. Each group of findings ends with one sentence that names a form the checker passes. Use `off` for work that requires such wording. Running the checker manually still reports the same matches.

Rules scan each line, then each paragraph for a phrase that wraps onto the next line. A finding carries the line where the phrase starts. The `dash-pair-list` rule scans paragraphs too and can find a list whose opening and closing dashes are on different lines.

## Add the skill to a project

Copy `skills/grounded-copy/` into `.style/grounded-copy/` in your project. Keep the whole directory so the examples and checker remain available.

```text
.style/grounded-copy/
├── SKILL.md
├── references/
├── scripts/copy_lint.py
└── tests/
```

Add this instruction to the project's `CLAUDE.md`, `AGENTS.md`, or the instruction file used by your agent:

```markdown
Read `.style/grounded-copy/SKILL.md` when writing or editing prose.
Select facts relevant to the task, keep claims accurate, and follow the user's requested style.
Run `python3 .style/grounded-copy/scripts/copy_lint.py <changed files>`.
Rewrite flagged copy and rerun the check. Keep the checker intact.
Report the result for files you checked.
```

### Check files in CI

Add a command for the files your project publishes:

```bash
python3 .style/grounded-copy/scripts/copy_lint.py README.md content/product.md
```

Use your actual file paths. Add `--profile chat` to run the contrast rules alone; with no option the checker runs every rule. Configure the CI job to fail on a nonzero exit code. This makes the same check available for edits from any contributor. A custom host hook can also call the checker, but its file paths and input format depend on the host.

## Check files as the agent saves them

The plugin ships an optional hook, `hooks/grounded_gate.py`, for Claude Code and Codex. After the agent writes or edits a file, the hook runs the checker on it under your saved profile. It hands any findings back to the agent, which rewrites the sentences and saves again. The `off` profile skips the check.

The hook checks `.md` and `.txt` files and any file under a `locale` or `locales` folder.

A sentence you typed in the session passes. The hook reads your messages from the session transcript and keeps a flagged sentence when it equals one of your sentences, a span you put in quotation marks, the text after a colon, or one of your list items. When a save holds only kept sentences, the host shows you a short message and the agent hears nothing.

Add the hook to your Claude Code `settings.json`. Point it at a clone of this repository, since a plugin cache path changes with each update:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "sh \"/path/to/grounded-copy/hooks/run.sh\" grounded_gate.py"
          }
        ]
      }
    ]
  }
}
```

On Windows with no Git Bash, use `cmd /d /c "C:\path\to\grounded-copy\hooks\run.cmd" grounded_gate.py` as the command.

On Codex, add the entry to `config.toml`. Point it at the `hooks` folder of the Codex package, which reads the Codex profile:

```toml
[[hooks.PostToolUse]]
matcher = "apply_patch"

[[hooks.PostToolUse.hooks]]
type = "command"
command = 'sh "/path/to/grounded-copy/dist/codex/grounded-copy/hooks/run.sh" grounded_gate.py'
commandWindows = 'cmd /d /c "C:\path\to\grounded-copy\dist\codex\grounded-copy\hooks\run.cmd" grounded_gate.py'
```

Codex passes the hook the patch it applied, and the hook checks each file that patch added, updated, or moved.

Limits:

- A draft you pasted counts as your text.
- A file the agent writes through a shell command goes unchecked on both hosts.
- In Claude Code, text you type into a permission prompt or a plan-rejection box reaches the transcript as a tool result, and the hook leaves tool results out. Send such a sentence as a normal message.
- In the Codex app, a plan you approved reaches the agent as a message from the app. The hook leaves that message out, so a sentence of the plan earns no pass.
- The pass relies on the mark each host puts on a typed prompt in its transcript, and neither host documents that format. A version with no such mark gives no pass, and every finding reports.
- The hook trusts the transcript file. The skill's integrity rules forbid an agent from writing to it.

## Turn off or remove an installation

To pause the writing rules, select the `off` profile. To remove installations managed by the installer, run this from a repository clone:

```bash
python3 install.py --uninstall --dry-run
python3 install.py --uninstall
```

Review the preview to see which host commands will run. A skill copied manually into a project can be removed with its instruction-file entry.
