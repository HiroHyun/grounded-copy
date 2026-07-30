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
| Does `${CLAUDE_PLUGIN_DATA}` resolve for `@skills-dir`? | Yes — `~/.claude/plugins/data/grounded-copy-skills-dir`. The flag still uses a fixed path (see below) |
| Command name | `/grounded-copy:grounded`; plain `/grounded` returns "Unknown command" |

The flag lives at `<config-dir>/grounded-copy/profile`, one fixed path for
every install. `${CLAUDE_PLUGIN_DATA}` earns its keep for a
marketplace plugin, whose `${CLAUDE_PLUGIN_ROOT}` moves into a new cache
directory on update; a plugin discovered in a skills directory is read in
place, so the root holds still. The flag also holds user state, which belongs
somewhere the user can cat, edit, and grep while debugging the switch.

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

Every failure ends in exit 0 with no traceback: a missing interpreter, malformed
stdin, an oversized flag file, and a symlinked flag file. A style reminder that
breaks a session start costs more than the reminder is worth.

Each launcher forwards its arguments as the shell parsed them. `run.cmd` runs
with delayed expansion off and passes `%2` through `%9`, which caps it at eight
arguments after the script name; both hook commands pass two. Delayed expansion
consumed `!` inside an argument, so `co!py` reached the hook as `copy` and wrote
the `copy` profile.

### Profiles

Three names: `chat`, `copy`, `off`. `chat` is the default and the stored value
for the core rules; a flag written as `technical` by an earlier install reads as
`chat`.

| Profile | Session block | Per-turn reminder |
|---|---|---|
| `chat` | intro with its example pair, the banned move with its ten disguises and the repair, the factual-negation test — 3,027 bytes | one line naming `chat` |
| `copy` | the same, plus four closures covering quotes and testimonials, headline and CTA scope, translation, and the linter's standing as a floor — 4,143 bytes | one line naming `copy` |
| `off` | none | none |

Two switch paths, one writer. `grounded_tracker.py` performs every write,
reached either by `/grounded-copy:grounded chat|copy|off`, which runs the
script with `--set`, or by a prompt whose whole text is a control instruction,
which the hook parses.

Both paths exist because a prompt starting with `/` is resolved as a slash
command before any `UserPromptSubmit` event fires. Measured: typing
`/grounded copy` when no such command is registered prints "Unknown command"
and the hook never receives the text, so command-name parsing inside the hook
cannot carry the switch alone. Both paths reach the same fixed flag path, so a
hook run and a shell run need no coordination.

The parser matches a control instruction against the whole prompt, under a
64-character cap, and a trailing `?` falls outside every form. An unanchored
search matched the words wherever they sat, so a quoted error string, a pasted
line, or a note about this file each wrote a value that the transcript never
reported. `off` is the value that silences both hooks, which made an accidental
switch look like an ordinary session with the block scrolled past.

### Reading and restoring the profile

```bash
python hooks/grounded_tracker.py --status
python hooks/grounded_tracker.py --set chat
```

`--status` reports the profile, its source, and the resolved path, and exits 0
in every state:

| Flag file | Resolved | `--status` reports |
|---|---|---|
| absent | `chat` | `(default, no flag at PATH)` |
| `chat`, or legacy `technical` | `chat` | `(recorded at PATH)` |
| `copy` | `copy` | `(recorded at PATH)` |
| `off` | `off` | `(recorded at PATH); run --set chat to restore` |
| symlink, over 64 bytes, or an unrecognized value | `chat` | `(default, unreadable flag at PATH)` |

`resolve_profile()` in `hooks/_payload.py` is the one place this table is
implemented, and both hooks call it, so the two entry points agree on every
input. Neither hook writes the flag; the file appears when a user selects a
profile.

### Tests

```bash
python hooks/grounded_activate.py --self-test
python -m unittest discover -s tests -p 'test_*.py'
```

The suite drives both CLI entry points through `subprocess` with
`CLAUDE_CONFIG_DIR` pointed at a temporary directory, so it reads and writes
nothing outside it. `tests/test_launchers.py` covers argument forwarding and
skips the `run.cmd` cases off Windows. CI runs both files on `ubuntu-latest`
and `windows-latest`.

### Dev loop

`SKILL.md` edits apply live in the current session. Changes under `hooks/`
need `/reload-plugins` or a restart.

### Rollback

`claude plugin disable grounded-copy@skills-dir` stops the hooks and leaves
the skill in place. Deleting `.claude-plugin/` and restarting returns the
folder to a plain skill.

### Phase 2 evidence gate

Phase 1 injects text and lints nothing. The deterministic output gates — the
`Stop` hook, the file gate, and the commit-body gate — ship against counted
drift with layers A and B already running. One row per observed slip:

| Date | Banned move | Surface | Layers active |
|---|---|---|---|
| 2026-07-30 | appositive reversal | fenced block in a chat reply | A and B |
| 2026-07-30 | bare "rather than" contrast | fenced block in a chat reply | A and B |

Counting method: record a row when a banned move reaches user-visible output
with a profile active, naming the move, the surface, and the layers running.
Both rows landed inside fenced blocks, which is why the deferred spec selects
fences by language tag and keeps untagged fences in scope.

The per-turn reminder stays in Phase 1 for a role `SessionStart` leaves open:
per-turn recency against the per-turn injections other plugins make, with
caveman writing `additionalContext` on every turn in this configuration.
`SessionStart` returns after each compaction and says nothing about the turns
between.

Two gaps in `scripts/copy_lint.py`, recorded here and carried as their own
change against `main`, one pattern per pull request per `CONTRIBUTING.md`:

- The prepositional appositive passes. `comma-not-appositive` matches
  `,\s*not\s+(?:a|an|another|your)`, so `, not from`, `, not on`, `, not by`,
  `, not in`, and `, not through` all clear the gate. Measured: "Decide from
  observed drift, not from a calendar." returns 0 findings; the same sentence
  ending "not a calendar" returns 1 WARN. Severity belongs at WARN, since
  factual uses exist, and the deletion test in `references/patterns.md` decides
  each case.
- Bare "rather than" sits at WARN, and the second slip above used that form.

Citation cost, measured while writing this branch: `README.md` produces 15
errors and 4 warnings on both `main` and this branch, every one a banned pattern
quoted as an example in the before/after table or the multilingual list. The
deferred `prose_gate.py` demotes a quoted or backticked ERROR to WARN in the
technical profile for this reason.

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
