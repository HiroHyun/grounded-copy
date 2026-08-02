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

`README.md` carries the install commands. This file covers what the plugin
wires up once it is installed.

The flag lives at `<config-dir>/grounded-copy/profile`, one fixed path across
every install method. A marketplace install copies the plugin into
`~/.claude/plugins/cache`, so its `${CLAUDE_PLUGIN_ROOT}` moves to a new
directory on each version; a plugin discovered in a skills directory is read in
place, so that root holds still. One fixed path keeps the two methods on the
same file, and it holds user state, which belongs somewhere the user can cat,
edit, and grep while debugging the switch. `${CLAUDE_PLUGIN_DATA}` does resolve
for `@skills-dir`, measured at `~/.claude/plugins/data/grounded-copy-skills-dir`
on Claude Code 2.1.220; the fixed path wins on the reason above.

A skill loads when the model judges its description relevant, and this
description covers copy tasks, so chat replies fall outside it. Two hooks put
the rules in every session instead.

`.claude-plugin/plugin.json` registers both hooks:

| Hook | Script | Output |
|---|---|---|
| `SessionStart` (no matcher) | `hooks/grounded_activate.py` | the session policy, 3,872 bytes under `chat`, repeated after each compaction |
| `UserPromptSubmit` | `hooks/grounded_tracker.py` | the turn reminder, 218 bytes |

Both hooks are read-only. `### Profile lifecycle` below defines every term
above and names the one path that records a preference.
`### Measured recurring cost` gives the figures and the method.

`_policy.py` reads `SKILL.md` at runtime and emits the intro with its example
pair plus four core sections: the banned move with its seven shapes, positive
forms, scope and precedence, and sourcing. Run
`python hooks/grounded_activate.py --self-test` after editing `SKILL.md`; it
asserts the structure, checks each payload against its published budget, and
prints the size delta against the recorded baseline.

Modules, split by domain responsibility:

| Module | Owns |
|---|---|
| `hooks/_preference.py` | the profile preference: value parsing, resolution, persistence, status line, write outcomes |
| `hooks/_policy.py` | `SKILL.md` extraction, session-policy assembly, the turn reminder, governing directives, the structure and budget self-test |
| `hooks/_hook_io.py` | hook transport: the stdin drain and plugin-root resolution |
| `hooks/grounded_activate.py` | the `SessionStart` entry point and `--self-test` |
| `hooks/grounded_tracker.py` | the `UserPromptSubmit` entry point, `--set`, and `--status` |
| `scripts/copy_lint.py` | the deterministic gate: patterns, findings, exit codes |
| `scripts/build_codex_adapter.py` | building the Codex adapter from the canonical files, and `--check` |

`_hook_io.py` earns its own file on use: both entry points call both of its
functions, and `plugin_root()` carries three resolution rules whose duplication
across two files is how they drift apart. Transport stays outside
the preference and policy vocabulary, so `_preference.py` reads no stdin and
`_policy.py` reads no environment.

### Launchers

Both hook commands call a launcher, which probes `python` then `python3`,
takes the first reporting Python 3, and runs the hook once.

`plugin.json` ships with `sh "${CLAUDE_PLUGIN_ROOT}/hooks/run.sh"`. On a
Windows setup where `sh` is absent from the hook shell, change both commands
to `"${CLAUDE_PLUGIN_ROOT}/hooks/run.cmd"`. The two launchers behave
identically, and each forwards its arguments verbatim, so paths holding
spaces survive. `run.cmd` forwards `%2` through `%9`, which caps it at eight
arguments after the script name; each hook command passes one.

Both launchers match the first argument against the two shipped script names
and assign a literal on match, so the executed command line derives from the
launcher file. An unknown name exits 0 with no output. Both hand the
interpreter's exit code back — `run.sh` through `exec`, `run.cmd` through
`exit /b %ERRORLEVEL%` — which the `--set` contract needs.

Every failure ends in exit 0 with no traceback: a missing interpreter, malformed
stdin, an oversized flag file, and a symlinked flag file. A style reminder that
breaks a session start costs more than the reminder is worth.

Each launcher's header comment records the bug its shape exists to prevent.

### Shell-facing values

Quoting is an assumption and model-side matching is a behavior; neither counts
as a security guarantee. Three value classes, three treatments:

| Value | Treatment | Residual |
|---|---|---|
| script name | closed-set dispatch in both launchers | none: the executed string is a literal from the file |
| profile value | `commands/grounded.md` interpolates nothing; every command line in it is a constant, and `canonical_argument()` rejects anything outside the closed set with exit 2 | a model could compose a line the file does not contain; the permission prompt is the boundary |
| plugin root | open | a shell metacharacter in the plugin root |

The manifest writes `sh "${CLAUDE_PLUGIN_ROOT}/hooks/run.sh"`. That form works
under two mechanisms — Claude Code substituting the token before the shell
parses the line, or `sh` expanding it from the environment — and a working state
tells them apart in neither direction. The quoting holds at the double-quoted
form until a live host measurement says which one runs. It blocks nothing that
ships.

`plugin_root()` reads `$CLAUDE_PLUGIN_ROOT` from the environment and falls back
to the hooks directory's parent, so the hook commands pass no `--plugin-root`.
The flag stays supported for the suite and manual runs.

`tests/test_launchers.py` drives a plugin root named ``gc $t`e;s&t v`` through
both launchers, with `"` added on POSIX where the filesystem permits it. That
bounds the launchers themselves; the shell parsing that precedes them lives at
the manifest seam above.

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
interception needs an output-side gate — a `Stop` hook, a file gate, a
commit-body gate — and Phase 1 ships none of them, so a chat reply reaches the
user with no scan. The turn reminder holds a role `SessionStart` leaves open:
per-turn recency against the per-turn injections other plugins make.
`SessionStart` returns after each compaction and says nothing about the turns
between.

**Three names.** `chat`, `copy`, `off`. `chat` is the default and the stored
value for the core rules; a preference written as `technical` by an earlier
install reads as `chat`. `### Reading and restoring the preference` below gives
the words `--set` accepts.

| Profile | Session policy | Turn reminder |
|---|---|---|
| `chat` | the intro with its example pair, the banned move with its seven shapes, positive forms, scope and precedence, and sourcing — 3,766 bytes of rules | one line naming `chat` |
| `copy` | the same, plus the marketing register and two closures covering translation and the linter's standing as a floor — 5,429 bytes | one line naming `copy` |
| `off` | none | none |

`--self-test` prints those two figures and fails when a payload passes its
budget. `### Measured recurring cost` gives what each hook writes to stdout,
which adds 106 bytes to the rules, and the method behind both.

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

### Measured recurring cost

UTF-8 bytes of each hook's stdout, measured 2026-08-02 on Claude Code 2.1.220,
Windows 11.

| Payload | Bytes |
|---|---|
| `chat` session policy, per `SessionStart` | 3,872 |
| `copy` session policy, per `SessionStart` | 5,535 |
| turn reminder, per prompt | 218 |
| `chat` governing directive, per switch | 4,073 |
| `copy` governing directive, per switch | 5,736 |
| `SKILL.md`, loaded when the skill triggers | 8,707 |

**Two boundaries, one payload.** A session-policy row is the rules body plus
the header, the switch line, and the blank lines between them: 106 bytes.
`python hooks/grounded_activate.py --self-test` prints the body alone, which is
the figure `### Profile lifecycle` gives per profile. A governing directive is
that body plus 248 bytes plus the resolved preference path, which its header
interpolates, so both directive rows measure a 59-character path and move with
it.

One 60-turn `chat` session with one compaction and one profile switch:
3,872 × 2 + 218 × 60 + 4,073 = 24,897 bytes, against 41,594 before the payload
cut, a 40.1% reduction.

Every token figure in this repository is an estimate at bytes ÷ 4 and is
labelled as one. No token count here comes from a tokenizer.

**What the payload carries.** `SKILL.md` keeps the rule and the opener for each
of the seven shapes; `references/patterns.md` holds each shape's complete
trigger list beside its rewrites, and arrives when the skill loads. The turn
reminder carries one clause per boundary it keeps in reach and omits
`Prefer established positive terms`, which `## Positive forms` states at session
start.

### Distribution

Three compatible paths ship from this repository. `README.md` carries the user
commands for each.

| Path | Manifest | What it installs |
|---|---|---|
| portable skill (Skills CLI) | none; the root `SKILL.md` is the skill source | `SKILL.md`, both references, `copy_lint.py` |
| Claude Code marketplace | `.claude-plugin/marketplace.json`, plus `.claude-plugin/plugin.json` | the whole repository as one plugin: skill, hooks, command |
| Codex marketplace | `.agents/plugins/marketplace.json`, plus the adapter's `.codex-plugin/plugin.json` | `adapters/codex/grounded-copy`: skill, references, linter, sample corpora |

The Claude Code marketplace lists one plugin whose `source` is `"./"`, so the
repository root is the plugin. `"skills": ["./"]` names the root `SKILL.md`
explicitly, which fixes the skill's invocation name to the frontmatter `name`
on every version; the auto-load of a root `SKILL.md` needs 2.1.142 or later.
A relative source resolves against a local copy of the marketplace, so users
add this marketplace from git; a direct URL to the JSON file downloads that
file alone and leaves the relative source unresolved.

The Codex plugin specification places skills at `skills/<skill-name>/SKILL.md`,
and the Skills CLI and Claude Code both read the repository-root `SKILL.md`.
`scripts/build_codex_adapter.py` resolves that by copying the canonical files
into the adapter byte-for-byte and writing the two files the adapter owns, its
manifest and its README. `--check` compares and exits 1 on any difference, and
CI runs it on both platforms, so the reuse claim is a tested property.

The adapter is skills-only by design: it ships the skill, `references/`,
`copy_lint.py`, and both sample corpora, and it ships no `hooks/`, no
`commands/`, and no `.claude-plugin/`. `tests/test_codex_adapter.py` asserts
that absence alongside byte identity and the MIT notice.

Measured on codex-cli 0.144.1, Windows 11, against this repository as a local
marketplace source:

| Question | Result |
|---|---|
| Which catalog does Codex read when a repository carries both? | `.agents/plugins/marketplace.json`. `codex plugin list` prints that path under the marketplace name, and the legacy `.claude-plugin/marketplace.json` alongside it stays unread |
| Does the local source resolve? | Yes — `grounded-copy@hirohyun-plugins` resolves to `adapters/codex/grounded-copy` |
| Subcommand names | `codex plugin add` and `codex plugin remove`; `install` and `uninstall` return "unrecognized subcommand". Marketplace verbs are `add`, `list`, `upgrade`, `remove` |
| Install location | `~/.codex/plugins/cache/hirohyun-plugins/grounded-copy/0.2.0`, holding the manifest, `LICENSE`, `README.md`, and `skills/grounded-copy/` |
| Does the linter run from the installed copy? | Yes — `good-samples.md` exits 0 and `bad-samples.md` exits 1 from the cache path |

The two catalogs carrying one name is settled by that first row: Codex reads
only `.agents/`, and Claude Code reads only `.claude-plugin/`, so the shared
name `hirohyun-plugins` names one catalog per host with no collision.

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

`--set` accepts the three profile names plus two aliases: `technical` for the
legacy stored value, and `marketing` for `copy`. Every other word exits 2 with
the message naming the three. `--set` outranks `--set --status` given together,
since it prints the status line itself.

`--set` exit codes: 0 recorded, 1 persistence failure, 2 rejected value. An
empty value reports status and exits 0, since it requests no change. A
recorded write reads the file back and confirms the stored value, so a write
landing somewhere the resolver cannot use reports failure at the moment it
happens. A symlink at the preference path exits 1 and names it: the resolver
already reads one as unreadable, and `write_preference()` leaves a file the
user placed there alone. The hook path keeps the exit-0 policy for every
internal failure.

### Tests

```bash
python hooks/grounded_activate.py --self-test
python scripts/build_codex_adapter.py --check
python -m unittest discover -s tests -p 'test_*.py'
```

The suite drives both CLI entry points through `subprocess` with
`CLAUDE_CONFIG_DIR` pointed at a temporary directory, so it reads and writes
nothing outside it. One class per domain term:
`SessionPolicyTests`, `TurnReminderTests`, `PreferenceResolutionTests`,
`ReadOnlyHookTests`, `GoverningDirectiveTests`, `SetAndStatusTests`.
`tests/test_launchers.py` covers argument forwarding, closed-set dispatch,
exit-code propagation, and hostile paths, and skips the `run.cmd` cases off
Windows. `tests/test_codex_adapter.py` covers byte identity against the
canonical files, the manifest fields, the MIT notice, the skills-only scope,
and a red-capable drift case that modifies a copy and asserts `--check` exits
1. CI runs all three files on `ubuntu-latest` and `windows-latest`.

These are the deterministic criteria. Whether the model then follows the
injected text is behavioral, and `**Enforcement boundary**` above states what
Phase 1 does about it.

Promoting every rule to blocking made two `tests/good-samples.md` lines fail,
a required disclaimer and a billing fact. Both moved to `tests/bad-samples.md`,
and the `off` profile is what a writer reaches for when copy has to carry one
of those forms.

### Dev loop

`SKILL.md` edits apply live in the current session. Changes under `hooks/`
need `/reload-plugins` or a restart.

A clone made before `.gitattributes` pinned the line endings keeps its original
bytes for every file a later pull leaves untouched, and
`scripts/build_codex_adapter.py --check` reports drift on that file alone.
Measured 2026-08-01 on a skills-directory clone: the root `LICENSE` sat at 1,086
bytes with CRLF while the adapter copy arrived in the same pull at 1,065 with
LF, so `--check` printed `codex adapter differs`. `git add --renormalize .` in
the clone applies the current rules to every tracked file and clears it.

### Rollback

`claude plugin disable grounded-copy@skills-dir` stops the hooks and leaves
the skill in place. Deleting `.claude-plugin/` and restarting returns the
folder to a plain skill.

### Citation cost and open scope

Every banned pattern this repository documents is quoted as the example that
defines it, so each file reports findings against its own gate. Measured
2026-08-02: `README.md` 17, `SKILL.md` 53, `references/patterns.md` 148, and
this file 0. CI runs `copy_lint.py` on `tests/bad-samples.md` and
`tests/good-samples.md` and on no other path, which is what keeps the rest
shippable. Sighting quotes belong in `references/patterns.md`; this file names
counts and holds none of its own.

**Wrapped-phrase acceptance requirement.** One scope stands open.
`scan_line()` scans one line at a time, so a comparison phrase whose two halves
land on either side of a Markdown line wrap produces zero findings. Every file
in this repository is hard-wrapped near column 76, so the exemption already
applies to the shipped corpus. Requirement: a phrase split across a wrap
reports the same finding as the same phrase on one line, with the line number
pointing at the first line of the match. A red-capable test writes each shipped
multi-word pattern in both forms and asserts the finding counts match.
Formatting creates no exemption.

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

Two routes, and they compose.

**The marketplace.** `codex plugin marketplace add HiroHyun/grounded-copy`
registers the catalog at `.agents/plugins/marketplace.json`, and
`codex plugin add grounded-copy@hirohyun-plugins` installs the adapter from
`adapters/codex/grounded-copy`. `codex /plugins` does the same interactively.
`### Distribution` above covers what the adapter carries, what it leaves to
Claude Code, and the measured CLI behavior.

**`AGENTS.md`.** Codex reads it from the repo root, which reaches a project
checkout with no install step:

```markdown
## Copy style (mandatory)

Read `.style/grounded-copy/SKILL.md` before producing any user-facing copy.
Run `python3 .style/grounded-copy/scripts/copy_lint.py <files>` and iterate
until it exits 0. Do not modify the linter.
```

A Codex plugin may register lifecycle hooks under `hooks/hooks.json`, and Codex
holds them untrusted until the user reviews the definition. This adapter ships
none, so CI is the backstop for the Codex path.

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
loophole, where an agent "fixes" the gate and leaves the copy alone.
