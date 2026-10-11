# Setup

Start with the installation commands in the [English README](https://github.com/HiroHyun/grounded-copy#readme) or [中文说明](https://github.com/HiroHyun/grounded-copy/blob/main/README.zh.md). This guide explains how to check an installation, change profiles, and run the checker in a project.

## Check your installation

In Claude Code, run `/grounded-copy:grounded`. In Codex, run `$grounded-profile status`. The result shows the active profile and where the setting is saved.

The default is `chat`. Try asking the agent to rewrite a short paragraph using grounded-copy. To check a saved file, see [Check a file](#check-a-file).

The Skills CLI installation includes the writing rules, examples, checker, and sample files. Saved profiles, session reminders, and the check on saved files come with the Claude Code and Codex plugins.

### Update

| Installed through | Run |
|---|---|
| Claude Code plugin | `claude plugin marketplace update hirohyun-plugins`, then `claude plugin update grounded-copy@hirohyun-plugins` |
| Codex plugin | `codex plugin marketplace upgrade hirohyun-plugins` |
| Skills CLI | `npx skills update` |

Codex stops a download after 30 seconds. If the upgrade times out, run it again. If it keeps failing, run `codex plugin marketplace remove hirohyun-plugins` and install again. Your saved mode stays.

After updating a plugin, reload it and start a new session to load the revised rules. For a manually copied skill, replace the complete skill directory so its references stay in sync.

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

A skill loads when the agent judges it relevant. To have every session apply it, add `--always-on`:

```bash
python3 install.py --skills-only --always-on
```

The installer writes a short marked block into `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md`. It skips a host that gets its plugin in the same run, since the plugin already loads the rules. Run the command again to refresh the block. `--uninstall` removes it.

Run `python3 install.py --help` to see all options. The installer prints each host command before running it.

## Profile lifecycle

A profile is a saved writing mode. Use `chat` for everyday interaction and ordinary documents, `copy` for product pages, marketing copy, and similar text, and `off` for work that needs another style. Switch to `off` before translating source text whose wording and comparisons must be preserved.

| Action | Claude Code | Codex |
|---|---|---|
| Everyday interaction and documents | `/grounded-copy:grounded chat` | `$grounded-profile chat` |
| Product pages and marketing copy | `/grounded-copy:grounded copy` | `$grounded-profile copy` |
| Turn the rules off | `/grounded-copy:grounded off` | `$grounded-profile off` |
| Show the saved setting | `/grounded-copy:grounded` | `$grounded-profile status` |

The setting stays saved across restarts. Each host uses its own file:

| Host | Setting file |
|---|---|
| Claude Code | `$CLAUDE_CONFIG_DIR/grounded-copy/profile`, or `~/.claude/grounded-copy/profile` by default |
| Codex | `$CODEX_HOME/grounded-copy/profile`, or `~/.codex/grounded-copy/profile` by default |

What each profile adds to a session:

| Profile | Bytes at session start | Turn reminder |
|:---:|:---:|:---:|
| `chat` (default) | 4,032 | 238 bytes |
| `copy` | 6,224 | 238 bytes |
| `off` | 0 | none |

Those counts are the rules themselves. The hook adds 106 more bytes for its header and switch line.

The plugin reads this file at session start and after context compaction. It adds the selected writing rules to the agent's context. Each prompt also gets a short reminder of the profile.

A successful switch saves the setting and prints the instructions that apply from that point forward. Earlier instructions remain visible in the conversation. The new instructions tell the agent which profile to follow now.

Use the profile command to change modes during a session. A manual edit of the setting file changes the next reminder, but the full rules load at the next session start.

### Enforcement boundary

The session hook and the prompt hook give the agent instructions. A third hook checks the prose files the agent saves; see [Check files as the agent saves them](#check-files-as-the-agent-saves-them). A chat reply reaches you with no scan. To check any other file, run `copy_lint.py` on it or add it to your project's CI.

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

Claude Code runs plugin hooks in Git Bash when it finds one and in PowerShell otherwise. Each hook command dot-sources a launcher in `hooks/`, such as `claude_activate.cmd`, that both shells start. Git Bash reads the file as a shell script and runs `run.sh`. PowerShell runs it as a batch file, which hands over to `run.cmd`. The hooks work in either shell without edits to the manifest.

If an error shows a literal `${CLAUDE_PLUGIN_ROOT}` or `${PLUGIN_ROOT}`, the host did not substitute the plugin path. Check the plugin configuration before running the command again.

### Claude Code shows a duplicate skill

When both the Skills CLI copy and the plugin are installed, Claude Code may show `grounded-copy@skills-dir` as `Not loaded`. The active plugin supplies the skill and hooks. Check the plugin's status before reinstalling.

### The checker reports a sentence you need to keep

The checker matches text patterns. Some phrases also have ordinary factual uses. Read the sentence in context and preserve its meaning. Each group of findings ends with one sentence that names a form the checker passes. Use `off` for work that requires such wording. Running the checker manually still reports the same matches.

Rules scan each line, then each paragraph for a phrase that wraps onto the next line. A finding carries the line where the phrase starts. The `dash-pair-list` rule scans paragraphs too and can find a list whose opening and closing dashes are on different lines.

## Check a file

From a clone of this repository, run:

```bash
python3 skills/grounded-copy/scripts/copy_lint.py draft.md
```

Use `python` if that is your Python 3 command. You can pass several file paths in one call. Add `--profile chat` to check everyday writing. With no option, or with `--profile copy`, the checker runs every rule.

Each finding gives the file, the line, the matched text, and a rule name in brackets. Under each group of findings the checker prints one sentence that says what to cut.

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
```

### Check files in CI

Add a command for the files your project publishes:

```bash
python3 .style/grounded-copy/scripts/copy_lint.py README.md content/product.md
```

Use your actual file paths. Add `--profile chat` to check everyday writing; with no option the checker runs every rule. Configure the CI job to fail on a nonzero exit code. This makes the same check available for edits from any contributor. A custom host hook can also call the checker, but its file paths and input format depend on the host.

A finding prints as the file, the line, the matched text, and the rule name in brackets. Version 0.7.0 changed that line, so update a script that reads the earlier form.

## Check files as the agent saves them

The Claude Code and Codex plugins check each prose file the agent saves. After the agent writes or edits a file, a hook runs the checker on the text that save added, under your saved profile. It hands any findings back to the agent, which rewrites the sentences and saves again. Text that was already in the file is left alone. The `off` profile skips the check.

The hook checks `.md` and `.txt` files and any file under a `locale` or `locales` folder.

A sentence you typed in the session passes. The hook reads your messages from the session transcript and keeps a flagged sentence when it equals one of your sentences, a span you put in quotation marks, the text after a colon, or one of your list items. When a save holds only kept sentences, the host shows you a short message and the agent hears nothing.

In Codex, approve the new hook when the app asks for a review.

If you added this hook by hand from an earlier version of this guide, remove that entry. The plugin registers the hook now, and a second entry checks each save twice.

A skill installed with no plugin has no hooks. To add the check there, put the hook in your Claude Code `settings.json` and point it at a clone of this repository:

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

On Windows, Claude Code runs hooks in Git Bash when it finds one. Use the `sh` command above there too, with a path such as `C:/path/to/grounded-copy/hooks/run.sh`. On Windows with no Git Bash, hooks run in PowerShell, and the command is `cmd /d /c "C:\path\to\grounded-copy\hooks\run.cmd" grounded_gate.py; exit $LASTEXITCODE`. That `cmd` form fails under Git Bash.

On Codex, add the entry to `config.toml`. Point it at the `hooks` folder of the Codex package, which reads the Codex profile:

```toml
[[hooks.PostToolUse]]
matcher = "apply_patch"

[[hooks.PostToolUse.hooks]]
type = "command"
command = 'sh "/path/to/grounded-copy/dist/codex/grounded-copy/hooks/run.sh" grounded_gate.py'
commandWindows = 'cmd /d /c "C:\path\to\grounded-copy\dist\codex\grounded-copy\hooks\run.cmd" grounded_gate.py; exit $LASTEXITCODE'
```

Codex passes the hook the patch it applied, and the hook checks each file that patch added, updated, or moved.

On Windows, `exit $LASTEXITCODE` preserves the gate's exit code `2` through PowerShell. Codex uses that code to return findings to the agent. A command that omits it exits `1` when the gate reports findings, and Codex records a hook failure.

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
