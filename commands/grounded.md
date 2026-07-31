---
description: Show or switch the grounded prose profile
argument-hint: chat|copy|off
disable-model-invocation: true
---

Run exactly one of the four command lines below, then report what it prints
and change no other files. Pick the line by matching the argument you were
given against `chat`, `copy`, and `off`. An empty argument, or any other
value, takes the status line.

`chat`:

```bash
sh '${CLAUDE_PLUGIN_ROOT}/hooks/run.sh' grounded_tracker.py --set chat
```

`copy`:

```bash
sh '${CLAUDE_PLUGIN_ROOT}/hooks/run.sh' grounded_tracker.py --set copy
```

`off`:

```bash
sh '${CLAUDE_PLUGIN_ROOT}/hooks/run.sh' grounded_tracker.py --set off
```

Empty argument, or a value outside those three:

```bash
sh '${CLAUDE_PLUGIN_ROOT}/hooks/run.sh' grounded_tracker.py --status
```

Run the chosen line as written. This file interpolates no argument, so every
command line in it is a constant; composing a new one would put a user-typed
value on a shell command line.

For an unrecognized value, report the value that was rejected and the profile
the status line names. The preference file holds still.

Exit codes on `--set`: 0 recorded, 1 persistence failure, 2 rejected value.
`--status` exits 0 in every state.

A recorded switch prints a governing directive after the status line. That
directive supersedes every grounded-copy policy statement earlier in the
transcript and governs from that turn onward.

If a command line carries a literal dollar-brace placeholder where an absolute
path belongs, the substitution failed: report that and stop. On a Windows
setup where `sh` is absent from PATH, run the same script through
`hooks/run.cmd` with double quotes around the path, matching the launcher swap
in `references/setup.md`; `cmd` reads `'` as an ordinary character.

Profiles:

- `chat` — the core rules: the banned move with its seven shapes, the deletion
  test, positive forms, scope and precedence, and sourcing.
- `copy` — the same, plus the marketing register and two closures covering
  translation and the linter's standing as a floor.
- `off` — the session policy and the turn reminder both stop. The value
  persists across restarts until `chat` or `copy` replaces it.

`### Profile lifecycle` in `references/setup.md` is the one description of how
the profile preference, the session policy, the turn reminder, and the
effective policy relate. The preference lives at
`<config-dir>/grounded-copy/profile`, where config-dir is `$CLAUDE_CONFIG_DIR`
when set and `~/.claude` otherwise.
