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
| `SessionStart` (no matcher) | `hooks/grounded_activate.py` | the session policy, ~1,600 tokens, repeated after each compaction |
| `UserPromptSubmit` | `hooks/grounded_tracker.py` | the turn reminder, ~60 tokens |

Both hooks are read-only. `### Profile lifecycle` below defines every term
above and names the one path that records a preference.

`_policy.py` reads `SKILL.md` at runtime and emits five core sections: the
intro with its example pair, the banned move with its disguises, the deletion
test, positive forms, scope and precedence, and sourcing. Run
`python hooks/grounded_activate.py --self-test` after editing `SKILL.md`; it
asserts the structure and prints the size delta against the recorded baseline.

Five modules, split by domain responsibility:

| Module | Owns |
|---|---|
| `hooks/_preference.py` | the profile preference: value parsing, resolution, persistence, status line, write outcomes |
| `hooks/_policy.py` | `SKILL.md` extraction, session-policy assembly, the turn reminder, governing directives, the structure self-test |
| `hooks/_hook_io.py` | hook transport: the stdin drain and plugin-root resolution |
| `hooks/grounded_activate.py` | the `SessionStart` entry point and `--self-test` |
| `hooks/grounded_tracker.py` | the `UserPromptSubmit` entry point, `--set`, and `--status` |

`_hook_io.py` earns its own file on the deletion test: both entry points call
both of its functions, and `plugin_root()` carries three resolution rules whose
duplication across two files is how they drift apart. Transport stays outside
the preference and policy vocabulary, so `_preference.py` reads no stdin and
`_policy.py` reads no environment.

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
arguments after the script name; each hook command passes one. Delayed
expansion consumed `!` inside an argument, so `co!py` reached the hook as
`copy` and wrote the `copy` profile.

Both launchers match the first argument against the two shipped script names
and assign a literal on match, so the executed command line derives from the
launcher file. `run.cmd` re-expands `%SCRIPT%` into that line, which is the
reason the closed set exists. An unknown name exits 0 with no output.

Both launchers hand the interpreter's exit code back — `run.sh` through `exec`,
`run.cmd` through `exit /b %ERRORLEVEL%` — which the `--set` contract needs.
`run.cmd` ended at `exit /b 0` before, which masked every result the hook
reported.

### Shell-facing values

Quoting is an assumption and model-side matching is a behavior; neither counts
as a security guarantee. Three value classes, three treatments:

| Value | Treatment | Residual |
|---|---|---|
| script name | closed-set dispatch in both launchers | none: the executed string is a literal from the file |
| profile value | `commands/grounded.md` interpolates nothing; every command line in it is a constant, and `canonical_argument()` rejects anything outside the closed set with exit 2 | a model could compose a line the file does not contain; the permission prompt is the boundary |
| plugin root | open — see the measurement below | a shell metacharacter in the plugin root |

The manifest writes `sh "${CLAUDE_PLUGIN_ROOT}/hooks/run.sh"`. That form works
under two different mechanisms — Claude Code substituting the token before the
shell parses the line, or `sh` expanding it from the environment — and the
working state alone tells them apart in neither direction. Tightening the
quoting needs the measurement first:

1. Register a temporary `SessionStart` command that writes its environment and
   its own argv to a file, run `/reload-plugins`, and start one session.
2. Exported and unsubstituted: switch the manifest to
   `sh "$CLAUDE_PLUGIN_ROOT/hooks/run.sh"`. A parameter expansion inside double
   quotes undergoes no word splitting and no re-parsing, so the path is data by
   the shell's own rules.
3. Substituted: the path is textual, and single quotes are the strongest
   available control, with a literal `'` in the root as the residual. The
   `run.cmd` variant keeps double quotes, since `cmd` reads `'` as an ordinary
   character.

`--plugin-root "${CLAUDE_PLUGIN_ROOT}"` came out of both hook commands as a
second interpolation with no purpose: `plugin_root()` reads
`$CLAUDE_PLUGIN_ROOT` from the environment and falls back to the hooks
directory's parent. The flag stays supported for the suite and manual runs.

`tests/test_launchers.py` drives a plugin root named ``gc $t`e;s&t v`` through
both launchers, with `"` added on POSIX where the filesystem permits it. That
bounds the launchers. The shell parsing that precedes them lives at the
manifest seam, which the live check above covers.

### Profile lifecycle

This subsection is the one description of how the four pieces relate. Every
other surface points here.

| Term | Definition | Where it lives |
|---|---|---|
| profile preference | the value stored on disk | `<config-dir>/grounded-copy/profile` |
| session policy | the policy text `SessionStart` injects | `grounded_activate.py` stdout |
| turn reminder | the line `UserPromptSubmit` injects | `grounded_tracker.py` `additionalContext` |
| effective policy | the latest intended governing state | the most recent governing directive in the transcript |

**Enforcement boundary.** `SessionStart` and the turn reminder write into the
model's context. Both are read-only with respect to model output: they observe
nothing the model produces and block nothing. Everything they achieve is
guidance, and compliance with guidance is probabilistic. Deterministic
interception needs an output-side gate — the `Stop` hook, the file gate, and
the commit-body gate deferred to Phase 2 below.

**Three names.** `chat`, `copy`, `off`. `chat` is the default and the stored
value for the core rules; a preference written as `technical` by an earlier
install reads as `chat`.

| Profile | Session policy | Turn reminder |
|---|---|---|
| `chat` | the intro with its example pair, the banned move with its disguises, the deletion test, positive forms, scope and precedence, and sourcing — 6,333 bytes | one line naming `chat` |
| `copy` | the same, plus the marketing register and four closures covering quotes and testimonials, headline and CTA scope, translation, and the linter's standing as a floor — 8,590 bytes | one line naming `copy` |
| `off` | none | none |

The core grew from 3,027 bytes when scope, precedence, the deletion test,
positive forms, and sourcing moved into it, which roughly doubles the
per-session cost. `--self-test` prints the current figure.

**One writer, one path.** `_preference.write_preference()` is the sole writer
and `grounded_tracker.py --set` is its only caller.
`/grounded-copy:grounded chat|copy|off` runs that path. A `/` prompt resolves
as a slash command before any `UserPromptSubmit` event fires, which is why the
command file owns the switch: measured, typing `/grounded copy` when no such
command is registered prints "Unknown command" and the hook receives nothing.

**A transcript is append-only.** Policy text injected earlier in a session
stays there for the rest of it, so a switch reaches the effective policy by
issuing a new governing directive. `--set` prints one after the status line,
and its stdout reaches the transcript as a tool result in the same turn the
user typed the command:

| Transition | What `--set` prints | Effective policy after the turn |
|---|---|---|
| `off` → `chat`/`copy` | the whole session policy for the new profile | that profile's rules |
| `chat` → `copy` | the whole session policy for `copy` | core rules plus the marketing register |
| `copy` → `chat` | the whole session policy for `chat` | the core rules |
| any → `off` | the header and the supersession sentence | none |

The directive is self-contained, so every transition takes one code path with
no ordering assumptions. It supersedes the earlier statements and claims no
erasure: they stay readable in the transcript as a record, and the newest
directive states what governs from that turn onward.

Compaction self-heals: the next `SessionStart` reads the stored preference and
injects the matching session policy.

**Out-of-band bound.** A preference changed outside the command — a hand edit
during debugging — reaches the turn reminder's label on the next turn and the
session policy at the next `SessionStart`. Session-scoped state would close
that gap; this bound is the documented behavior in its place.

**Two rejection contracts.** `commands/grounded.md` executes constant command
lines, so an invalid argument reaches no process. Direct CLI rejection and
slash-command rejection are separate:

| Path | Observable |
|---|---|
| `grounded_tracker.py --set bogus` | exit 2, `grounded: unknown profile 'bogus'; choose chat, copy, or off`, preference held still |
| `/grounded-copy:grounded bogus` | Claude runs the `--status` constant; the preference file stays byte-identical, and the reply names the rejected value |

**Removed: the natural-language switch.** An earlier build parsed whole-prompt
control instructions inside the hook. `f1684bc` records the cost: three
ordinary prompts each wrote a persistent value that the transcript never
reported, `off` being the value that silences both hooks. Containing it took
four anchored forms, a 64-character cap, prompt normalization, a non-string
guard, and eight regression prompts. `8cca077` added `--set` and the command
file to cover the slash path, which closed the same gap. No commit, test, or
document records a benefit the slash command lacks, so the parser came out.
`ReadOnlyHookTests` keeps all seventeen prompts as the invariant: no prompt
records a preference.

### Reading and restoring the preference

```bash
python hooks/grounded_tracker.py --status
python hooks/grounded_tracker.py --set chat
```

`--status` reports the profile, its source, and the resolved path, and exits 0
in every state:

| Preference file | Resolved | `--status` reports |
|---|---|---|
| absent | `chat` | `(default, no preference at PATH)` |
| `chat`, or legacy `technical` | `chat` | `(recorded at PATH)` |
| `copy` | `copy` | `(recorded at PATH)` |
| `off` | `off` | `(recorded at PATH); run --set chat to restore` |
| symlink, over 64 bytes, or an unrecognized value | `chat` | `(default, unreadable preference at PATH)` |

`resolve_preference()` in `hooks/_preference.py` is the one place this table is
implemented, and both hooks call it, so the two entry points agree on every
input. It is read-only, and so are both hooks; the file appears when a user
selects a profile.

`--set` exit codes: 0 recorded, 1 persistence failure, 2 rejected value. An
empty value reports status and exits 0, since it requests no change. A
recorded write reads the file back and confirms the stored value, so a write
landing somewhere the resolver cannot use reports failure at the moment it
happens. The hook path keeps the exit-0 policy for every internal failure.

### Tests

```bash
python hooks/grounded_activate.py --self-test
python -m unittest discover -s tests -p 'test_*.py'
```

The suite drives both CLI entry points through `subprocess` with
`CLAUDE_CONFIG_DIR` pointed at a temporary directory, so it reads and writes
nothing outside it. One class per domain term:
`SessionPolicyTests`, `TurnReminderTests`, `PreferenceResolutionTests`,
`ReadOnlyHookTests`, `GoverningDirectiveTests`, `SetAndStatusTests`.
`tests/test_launchers.py` covers argument forwarding, closed-set dispatch,
exit-code propagation, and hostile paths, and skips the `run.cmd` cases off
Windows. CI runs both files on `ubuntu-latest` and `windows-latest`.

These are the deterministic criteria. Whether the model then follows the
injected text is behavioral, measured by observation and recorded as evidence
rows below.

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

The turn reminder stays in Phase 1 for a role `SessionStart` leaves open:
per-turn recency against the per-turn injections other plugins make, with
caveman writing `additionalContext` on every turn in this configuration.
`SessionStart` returns after each compaction and says nothing about the turns
between.

### Follow-up review scopes

`CONTRIBUTING.md` caps a pull request at one pattern, and separate commits on
one branch still ship as one pull request. Each row below is its own pull
request. `SKILL.md` already names the prepositional and absence forms, so the
guidance layer covers them today; the rows add the deterministic layer.

| Scope | Content | Red-capable test |
|---|---|---|
| prepositional contrast | widen `comma-not-appositive` to `,\s*not\s+(?:by\|from\|on\|in\|through\|with\|at\|for\|to\|via)\b`, WARN | rule name reported for the freshness sentence |
| absence framing, general | new `without-gerund` covering `adding\|needing\|requiring\|losing`, WARN | rule name reported for the index sentence |
| absence framing, rhetorical | new `without-sacrificing` covering `sacrificing\|compromising`, ERROR | a line in `tests/bad-samples.md`, exit 1 |
| bare exclusion clause | new `bare-instead-of` mirroring `bare-rather-than`, WARN | rule name reported |
| wrapped phrases | `scan_text()` gains a wrap-joined pass with line-offset mapping | see below |

Measured on this branch, both blind-spot sentences return
`0 error(s), 0 warning(s)`:

- "Freshness confirmed by query, not by the node count." → "The freshness query
  returned the current result."
- "It's the same code at the same commit, so a second index of it would add
  duplication without adding information." → "The existing index already
  represents that commit."

Both compliant forms also return `0 error(s), 0 warning(s)` and go into
`tests/good-samples.md` with the pattern that motivates them.

Both forms warrant WARN severity. WARN findings leave the process exit at zero,
so the red-capable test asserts each finding's rule name. Blocking findings
stay reserved for evidenced rhetorical forms with acceptable false-positive
rates. Bare "rather than" already sits at WARN, and the second slip above used
that form.

**Wrapped-phrase acceptance requirement.** `scan_line()` scans one line at a
time, so a comparison phrase whose two halves land on either side of a Markdown
line wrap produces zero findings. Every file in this repository is hard-wrapped
near column 76, so the exemption already applies to the shipped corpus.
Requirement: a phrase split across a wrap reports the same finding as the same
phrase on one line, with the line number pointing at the first line of the
match. A red-capable test writes each shipped multi-word ERROR pattern in both
forms and asserts the finding counts match. Formatting creates no exemption.

Citation cost, measured while writing this branch: `README.md` produces 15
errors and 4 warnings on both `main` and this branch, and `SKILL.md` produces
69 errors and 16 warnings, every one a banned pattern quoted as the example
that defines it. The deferred `prose_gate.py` demotes a quoted or backticked
ERROR to WARN in the technical profile for this reason.

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
