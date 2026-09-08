# Setup

Start with the installation commands in the [English README](https://github.com/HiroHyun/grounded-copy#readme) or [中文说明](https://github.com/HiroHyun/grounded-copy/blob/main/README.zh.md). This guide explains how to check an installation, change profiles, and run the checker in a project.

## Check your installation

In Claude Code, run `/grounded-copy:grounded`. In Codex, run `$grounded-profile status`. The result shows the active profile and where the setting is saved.

The default is `chat`. Try asking the assistant to rewrite a short paragraph using grounded-copy. To check a saved file, use the `copy_lint.py` command in the README.

The Skills CLI installation includes the writing rules, examples, checker, and sample files. Saved profiles and automatic session reminders come with the Claude Code and Codex plugins.

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

The plugin reads this file at session start and after context compaction. It adds the selected writing rules to the assistant's context. Each prompt also gets a short reminder of the profile.

A successful switch saves the setting and prints the instructions that apply from that point forward. Earlier instructions remain visible in the conversation. The new instructions tell the assistant which profile to follow now.

Use the profile command to change modes during a session. A manual edit of the setting file changes the next reminder, but the full rules load at the next session start.

### Enforcement boundary

The hooks provide instructions to the assistant. They do not inspect or block the assistant's output. A chat reply reaches you without an automatic copy scan. Run `copy_lint.py` on files you want to check, or add it to your project's CI.

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

The Claude manifest uses `sh "${CLAUDE_PLUGIN_ROOT}/hooks/run.sh"`. If `sh` is unavailable to Claude Code, change both hook commands in your installed plugin manifest to use the Windows launcher:

```text
"${CLAUDE_PLUGIN_ROOT}/hooks/run.cmd" grounded_activate.py
"${CLAUDE_PLUGIN_ROOT}/hooks/run.cmd" grounded_tracker.py
```

Keep double quotes around the path. Reload the plugin after editing the commands. An upgrade can replace edits in the installed cache.

If an error shows a literal `${CLAUDE_PLUGIN_ROOT}` or `${PLUGIN_ROOT}`, the host did not substitute the plugin path. Check the plugin configuration before running the command again.

### Claude Code shows a duplicate skill

When both the Skills CLI copy and the plugin are installed, Claude Code may show `grounded-copy@skills-dir` as `Not loaded`. The active plugin supplies the skill and hooks. Check the plugin's status before reinstalling.

### The checker reports a sentence you need to keep

The checker matches text patterns. Some phrases also have ordinary factual uses. Read the sentence in context and preserve its meaning. Use `off` for work that requires such wording. Running the checker manually still reports the same matches.

Most rules scan one line at a time. Phrases split over two lines can be missed. The `dash-pair-list` rule scans paragraphs and can find a list whose opening and closing dashes are on different lines.

## Add the skill to a project

Copy `skills/grounded-copy/` into `.style/grounded-copy/` in your project. Keep the whole directory so the examples and checker remain available.

```text
.style/grounded-copy/
├── SKILL.md
├── references/
├── scripts/copy_lint.py
└── tests/
```

Add this instruction to the project's `CLAUDE.md`, `AGENTS.md`, or the instruction file used by your assistant:

```markdown
Read `.style/grounded-copy/SKILL.md` when writing or editing prose.
Preserve the supplied facts and follow the user's requested style.
Run `python3 .style/grounded-copy/scripts/copy_lint.py <changed files>`.
Rewrite flagged copy and rerun the check. Keep the checker intact.
Report the result for files you checked.
```

### Check files in CI

Add a command for the files your project publishes:

```bash
python3 .style/grounded-copy/scripts/copy_lint.py README.md content/product.md
```

Use your actual file paths. Configure the CI job to fail on a nonzero exit code. This makes the same check available for edits from any contributor. A custom host hook can also call the checker, but its file paths and input format depend on the host.

## Turn off or remove an installation

To pause the writing rules, select the `off` profile. To remove installations managed by the installer, run this from a repository clone:

```bash
python3 install.py --uninstall --dry-run
python3 install.py --uninstall
```

Review the preview to see which host commands will run. A skill copied manually into a project can be removed with its instruction-file entry.
