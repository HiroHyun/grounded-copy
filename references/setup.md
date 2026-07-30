# Setup: one skill, both agents

The SKILL.md rules and `scripts/copy_lint.py` are agent-agnostic. Only the
loading mechanism differs. Vendor the folder into the repo once:

```
<repo>/
├── .style/grounded-copy/
│   ├── SKILL.md
│   ├── references/
│   └── scripts/copy_lint.py
├── CLAUDE.md
└── AGENTS.md
```

## Claude Code, always-on (plugin)

Measured on Claude Code 2.1.220, Windows 11:

| Question | Result |
|---|---|
| Does the Skills CLI deliver the plugin files? | Its `.source` manifest lists four files (`SKILL.md`, both references, `copy_lint.py`), and the install carries no `.git` directory, so `.claude-plugin/` and `hooks/` arrive by `git clone` only |
| Which launcher works? | `sh "${CLAUDE_PLUGIN_ROOT}/hooks/run.sh"` runs in the hook shell; `run.cmd` covers a setup lacking `sh` |
| Does `${CLAUDE_PLUGIN_DATA}` resolve for `@skills-dir`? | Yes — `~/.claude/plugins/data/grounded-copy-skills-dir/profile`. The `~/.claude/grounded-copy` fallback stays as insurance |
| Command name | `/grounded-copy:grounded`, alongside plain `/grounded` |

A skill loads when the model judges its description relevant, and this
description covers copy tasks, so chat replies fall outside it. Two hooks put
the rules in every session instead.

Clone the repo into the skills directory, which makes Claude Code load the
folder as `grounded-copy@skills-dir`:

```bash
git clone https://github.com/HiroHyun/grounded-copy ~/.claude/skills/grounded-copy
```

`.claude-plugin/plugin.json` registers both hooks:

| Hook | Script | Output |
|---|---|---|
| `SessionStart` (no matcher) | `hooks/grounded_activate.py` | the ruleset as session context, ~780 tokens, repeated after each compaction |
| `UserPromptSubmit` | `hooks/grounded_tracker.py` | a one-line reminder, ~45 tokens, plus the profile switch |

`grounded_activate.py` reads `SKILL.md` at runtime and emits three pieces: the
intro with its example pair, the whole banned-move section, and the
factual-negation bullet. Run `python hooks/grounded_activate.py --self-test`
after editing `SKILL.md`; it asserts the structure and prints the size delta
against the recorded baseline.

### Launchers

Both hook commands call a launcher, which probes `python` then `python3`,
takes the first reporting Python 3, and runs the hook once. The direct form

```
python X.py || python3 X.py
```

re-runs the script whenever the first interpreter exits nonzero for any
reason, which on `SessionStart` emits the ruleset twice.

`plugin.json` ships with `sh "${CLAUDE_PLUGIN_ROOT}/hooks/run.sh"`. On a
Windows setup where `sh` is absent from the hook shell, change both commands
to `"${CLAUDE_PLUGIN_ROOT}/hooks/run.cmd"`. The two launchers behave
identically, and each forwards its arguments verbatim, so paths holding
spaces survive.

Missing interpreter, malformed stdin, an oversized flag file, and a symlinked
flag file each end in exit 0 with no output. A style reminder that breaks a
session start costs more than the reminder is worth.

### Profiles

Two switch paths, one writer. `grounded_tracker.py` performs every write,
reached either by `/grounded-copy:grounded chat|copy|off`, which runs the
script with `--set`, or by plain words in a prompt ("switch grounded to copy",
"grounded prose off"), which the hook parses.

Both paths exist because a prompt starting with `/` is resolved as a slash
command before any `UserPromptSubmit` event fires. Measured: typing
`/grounded copy` when no such command is registered prints "Unknown command"
and the hook never receives the text, so command-name parsing inside the hook
cannot carry the switch alone. Shell runs find the data directory through
`~/.claude/grounded-copy/datadir.txt`, which every hook run rewrites.

Values persist at `$CLAUDE_PLUGIN_DATA/profile`, falling back to
`~/.claude/grounded-copy/profile` when that variable holds no path — the case
for a plugin discovered in place. `off` persists across restarts as an
explicit value; an absent flag reads as the `technical` default; anything
outside the three names reads as untrusted, and the tracker then emits
nothing.

### Dev loop

`SKILL.md` edits apply live in the current session. Changes under `hooks/`
need `/reload-plugins` or a restart.

### Rollback

`claude plugin disable grounded-copy@skills-dir` stops the hooks and leaves
the skill in place. Deleting `.claude-plugin/` and restarting returns the
folder to a plain skill.

## Claude Code, skill only

Install as a skill (auto-triggers on copy tasks):

```bash
mkdir -p ~/.claude/skills
cp -r .style/grounded-copy ~/.claude/skills/
```

Or, for repo-scoped enforcement that survives long sessions, add to
`CLAUDE.md`:

```markdown
## Copy style (mandatory)

Before writing, editing, or translating ANY user-facing copy — headlines,
value props, CTAs, meta descriptions, alt text, locale files — read
`.style/grounded-copy/SKILL.md` and follow it.

Every copy change must pass the gate before you report the task done:

    python3 .style/grounded-copy/scripts/copy_lint.py <changed files>

Exit code 1 means rewrite the flagged sentences and re-run. Never edit
copy_lint.py, add allowlists, or bypass the gate.
```

### Hard enforcement (hook)

`CLAUDE.md` is a request; a hook is a gate. In `.claude/settings.json`, run
the linter on every write to copy files and block the turn on failure:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "f=\"$CLAUDE_FILE_PATH\"; case \"$f\" in *.md|*.mdx|*.json|*.tsx|*.ts) python3 .style/grounded-copy/scripts/copy_lint.py \"$f\" || exit 2;; esac"
          }
        ]
      }
    ]
  }
}
```

Exit code 2 feeds the linter output back to the model and forces a rewrite.
This is the only layer that cannot be rationalized around.

## Codex

Codex reads `AGENTS.md` from the repo root. Add the same block:

```markdown
## Copy style (mandatory)

Read `.style/grounded-copy/SKILL.md` before producing any user-facing copy.
Run `python3 .style/grounded-copy/scripts/copy_lint.py <files>` and iterate
until it exits 0. Do not modify the linter.
```

Codex has no hook system, so CI is the backstop.

## Gemini

Point `GEMINI.md` (or the system instruction) at the same SKILL.md and the
same command. The rules are plain markdown; nothing is Claude-specific.

## CI backstop (catches every agent, including humans)

```yaml
# .github/workflows/copy-lint.yml
name: copy-lint
on: [pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          python3 .style/grounded-copy/scripts/copy_lint.py \
            $(git ls-files 'content/**/*.md' 'locales/*.json' 'src/**/*.tsx')
```

Add `.style/grounded-copy/scripts/copy_lint.py` to a CODEOWNERS entry so
edits to the linter itself require human review — that closes the last
loophole, where an agent "fixes" the gate instead of the copy.

## Layer summary

| Layer | Mechanism | Catches |
|---|---|---|
| SKILL.md rules | Probabilistic | Novel phrasings, cross-sentence contrast |
| `copy_lint.py` | Deterministic | 50+ enumerated patterns, 9 languages |
| Claude Code hook | Blocking | Anything written to disk in-session |
| CI + CODEOWNERS | Blocking | Every agent and human; linter tampering |
