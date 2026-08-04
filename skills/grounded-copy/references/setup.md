# Setup: one skill, both agents

The SKILL.md rules and `scripts/copy_lint.py` are agent-agnostic. Only the
loading mechanism differs.

The canonical directory is `skills/grounded-copy/` in the repository, and its
internal shape is what every install path carries: a Claude Code plugin
install, a `~/.claude/skills/grounded-copy` clone, a Skills CLI install, the
generated Codex package, and a vendored copy. Every path `SKILL.md` names
resolves against the directory holding it, so one pointer works everywhere.
Vendor the folder into the repo once:

```
<repo>/
├── .style/grounded-copy/
│   ├── SKILL.md
│   ├── references/
│   ├── scripts/copy_lint.py
│   └── tests/
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

A skill loads when the model judges its description relevant. The description
names chat replies, commit bodies, and code comments alongside the copy
surfaces, matching what `## Scope and precedence` governs, and the judgment is
still made per turn. Two hooks put the core rules in every session on a session
event instead, at 3,679 bytes where the skill costs 8,735.

`.claude-plugin/plugin.json` registers both hooks:

| Hook | Script | Output |
|---|---|---|
| `SessionStart` (no matcher) | `hooks/grounded_activate.py` | the session policy, 3,785 bytes under `chat`, repeated after each compaction |
| `UserPromptSubmit` | `hooks/grounded_tracker.py` | the turn reminder, 218 bytes |

Both hooks are read-only. `### Profile lifecycle` below defines every term
above and names the one path that records a preference.
`### Measured recurring cost` gives the figures and the method.

`_policy.py` reads `skills/grounded-copy/SKILL.md` under the plugin root at
runtime — the same relative path in a checkout, a plugin install, a clone, and
the Codex package — and emits the intro with its example pair plus four core
sections: the banned move with its seven shapes, positive forms, scope and
precedence, and sourcing. Run
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
| `skills/grounded-copy/scripts/copy_lint.py` | the deterministic gate: patterns, findings, exit codes |
| `scripts/build_codex_adapter.py` | building the Codex package from the canonical files, and `--check` |
| `install.py` | detecting agents and driving each host's own install verbs |

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
| `chat` | the intro with its grounded example, the banned move with its seven shapes, positive forms, scope and precedence, and sourcing — 3,679 bytes of rules | one line naming `chat` |
| `copy` | the same, plus the marketing register and two closures covering translation and the linter's standing as a floor — 5,140 bytes | one line naming `copy` |
| `off` | none | none |

`--self-test` prints those two figures and fails when a payload passes its
budget. `### Measured recurring cost` gives what each hook writes to stdout,
which adds 106 bytes to the rules under Claude Code, and the method behind
both. The Codex package runs 100 bytes: its switch line names
`$grounded-profile chat|copy|off`, six bytes shorter than the Claude slash
command, which the entrypoint seam supplies.

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
| `chat` session policy, per `SessionStart` | 3,785 |
| `copy` session policy, per `SessionStart` | 5,246 |
| turn reminder, per prompt | 218 |
| `chat` governing directive, per switch | 3,986 |
| `copy` governing directive, per switch | 5,447 |
| `SKILL.md`, loaded when the skill triggers | 8,735 |

**Two boundaries, one payload.** A session-policy row is the rules body plus
the header, the switch line, and the blank lines between them: 106 bytes under
Claude Code, 100 in the Codex package, whose switch line names the shorter
`$grounded-profile` verb.
`python hooks/grounded_activate.py --self-test` prints the body alone, which is
the figure `### Profile lifecycle` gives per profile. A governing directive is
that body plus 248 bytes plus the resolved preference path, which its header
interpolates, so both directive rows measure a 59-character path and move with
it.

One 60-turn `chat` session with one compaction and one profile switch:
3,785 × 2 + 218 × 60 + 3,986 = 24,636 bytes, against 41,594 before the payload
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

Three compatible paths ship from this repository, and `install.py` drives all
three from one command. `README.md` carries the user commands for each.

| Path | Manifest | What it installs |
|---|---|---|
| portable skill (Skills CLI) | none; `skills/grounded-copy/SKILL.md` is the skill source | the whole skill directory: `SKILL.md`, both references, `copy_lint.py`, both corpora |
| Claude Code marketplace | `.claude-plugin/marketplace.json`, plus `.claude-plugin/plugin.json` | the whole repository as one plugin: skill, hooks, command |
| Codex marketplace | `.agents/plugins/marketplace.json`, plus the package's `.codex-plugin/plugin.json` | `dist/codex/grounded-copy`: lifecycle hooks, skills, references, corpora, linter, and launchers |

The portable command reaches 17+ agents through one universal Skills CLI
install. The two plugin packages add session-event policy and stored profile
control for Claude Code and Codex.

| Capability | Portable, 17+ agents | Claude Code and Codex plugins |
|---|:---:|:---:|
| `SKILL.md` rules | yes | yes |
| `references/patterns.md` catalog and nine locale rule sets | yes | yes |
| `scripts/copy_lint.py` | yes | yes |
| `tests/` sample corpora | yes | yes |
| `SessionStart` policy, repeated after each compaction |  | yes |
| `UserPromptSubmit` turn reminder |  | yes |
| `chat`, `copy`, and `off` profiles with a stored preference |  | yes |
| Profile controller and governing directive |  | yes |

A skill description is evaluated for relevance on each turn. The plugin hooks
run on registered session events. `### Profile lifecycle` defines those events
and the stored preference; `### Measured recurring cost` records each payload.

The Claude Code marketplace lists one plugin whose `source` is `"./"`, so the
repository root is the plugin, laid out the way a Claude Code plugin is laid
out: `skills/`, `commands/`, `hooks/`, and `.claude-plugin/plugin.json`.
`"skills": ["./skills/"]` names the directory explicitly, which fixes the
skill's invocation name to the frontmatter `name` on every version and keeps
discovery off the generated tree under `dist/`. A relative source resolves
against a local copy of the marketplace, so users add this marketplace from
git; a direct URL to the JSON file downloads that file alone and leaves the
relative source unresolved.

**One canonical directory, three hosts.** The Codex plugin specification
places skills at `skills/<skill-name>/SKILL.md`, the Skills CLI reads the same
convention, and Claude Code reads `skills/` by default. `skills/grounded-copy/`
satisfies all three at once, so `scripts/build_codex_adapter.py` mirrors that
directory into the generated tree at the same relative path and generates the
package-owned hooks, controller skill, manifest, and README. Every path
`SKILL.md` names resolves in a checkout and in each install, which
`tests/test_hooks.py::test_every_path_skill_md_names_exists` asserts. `--check`
compares the complete inventory and exits 1 on any difference, and CI runs it
on both platforms, so the reuse claim is a tested property.

The Codex tree is a generated plugin: it ships `hooks/hooks.json`, the shared
hook runtime and launchers, `skills/grounded-copy/`, and the explicit
`skills/grounded-profile/` controller. The builder walks the skill directory,
so a new reference file ships with no builder edit; `__pycache__` and build
residue stay out. Claude-only files (`commands/`, `.claude-plugin/`) and the
repository's own Python suites stay behind. `tests/test_codex_adapter.py`
pins the inventory, asserts byte identity, and asserts the MIT notice.

`dist/` is generated and tracked. `--check` compares committed bytes, and the
Codex catalog points `codex plugin add` at that path inside a clone, so the
directory travels with the repository.

Measured on codex-cli 0.144.1, Windows 11, against this repository as a local
marketplace source:

| Question | Result |
|---|---|
| Which catalog does Codex read when a repository carries both? | `.agents/plugins/marketplace.json`. `codex plugin list` prints that path under the marketplace name, and the legacy `.claude-plugin/marketplace.json` alongside it stays unread |
| Does the local source resolve? | Yes — `grounded-copy@hirohyun-plugins` resolves to the catalog's `source.path`, `./dist/codex/grounded-copy` since 0.4.0 and `./adapters/codex/grounded-copy` when this was measured |
| Subcommand names | `codex plugin add` and `codex plugin remove`; `install` and `uninstall` return "unrecognized subcommand". Marketplace verbs are `add`, `list`, `upgrade`, `remove` |
| Install location | `~/.codex/plugins/cache/hirohyun-plugins/grounded-copy/<version>`, holding the manifest, `LICENSE`, `README.md`, and `skills/grounded-copy/`. The measurement predates the hooks work and the version bump; a 0.4.0 install also holds `hooks/` and `skills/grounded-profile/`, and each earlier version keeps its own cache directory until `codex plugin remove` clears it |
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
input. Codex resolves `$CODEX_HOME/grounded-copy/profile`, defaulting to
`~/.codex/grounded-copy/profile`; Claude keeps its existing config path.

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
canonical files, the pinned generated inventory, the manifest fields, the MIT
notice, one version number across four manifests, the `<version>` placeholder
that keeps a release out of README prose, the Codex profile verb, and
a red-capable drift case that builds the package into a temporary mirror,
confirms it checks clean, then drifts one copy and asserts `--check` exits 1.
`tests/test_corpus.py` asserts every per-locale rule fires on a line in
`skills/grounded-copy/tests/bad-samples.md`; 38 of the 57 English rules carry
no line yet, which is what bounds that assertion to the locale set.
`tests/test_installer.py` describes a machine and asserts the commands
`install.py` would run on it, so detection and command construction are
covered with no agent installed. CI runs all five files on `ubuntu-latest` and
`windows-latest`.

Two directories carry the name `tests`. `tests/` at the repository root holds
the Python suites; `skills/grounded-copy/tests/` holds the two corpora, which
travel with the skill because `SKILL.md` points a reader at them.

These are the deterministic criteria. Whether the model then follows the
injected text is behavioral, and `**Enforcement boundary**` above states what
Phase 1 does about it.

Promoting every rule to blocking made two `good-samples.md` lines fail,
a required disclaimer and a billing fact. Both moved to `bad-samples.md`,
and the `off` profile is what a writer reaches for when copy has to carry one
of those forms.

### Dev loop

`skills/grounded-copy/SKILL.md` edits apply live in the current session.
Changes under `hooks/` need `/reload-plugins` or a restart. Changes under
`skills/grounded-copy/` also want `python scripts/build_codex_adapter.py`, so
the generated tree keeps matching.

A clone made before `.gitattributes` pinned the line endings keeps its original
bytes for every file a later pull leaves untouched, and
`scripts/build_codex_adapter.py --check` reports drift on that file alone.
Measured 2026-08-01 on a skills-directory clone: the root `LICENSE` sat at 1,086
bytes with CRLF while the adapter copy arrived in the same pull at 1,065 with
LF, so `--check` printed `codex adapter differs`. `git add --renormalize .` in
the clone applies the current rules to every tracked file and clears it.

### Rollback

`claude plugin disable grounded-copy@skills-dir` stops the hooks and leaves
the skill in place. That verb is the documented rollback: the clone loads as a
plugin, whose skill sits at `skills/grounded-copy/SKILL.md`, so a plain-skill
fallback wants that inner directory copied to a skills directory of its own.

### Citation cost and open scope

Every banned pattern this repository documents is quoted as the example that
defines it, so each file reports findings against its own gate. Measured
2026-08-04: `references/patterns.md` 181; `README.md` 12; `README.zh.md` 5; and
`SKILL.md`, `CONTRIBUTING.md`, `commands/grounded.md`, `install.py`, and this
file 0 each. Each front page carries its blocked drafts beside their rewrites
and two `without-gerund` triggers in its profile callout; the English page adds
four CJK triggers in its translation paragraph, and the catalog carries the full
set. `tests/citations-baseline.txt` records the rule id and snippet each of
those three files carries, and `scripts/check_citations.py` fails CI when that
set moves. `copy_lint.py` itself runs in CI on
`skills/grounded-copy/tests/bad-samples.md` and
`skills/grounded-copy/tests/good-samples.md` and on no other path, which is
what keeps the rest shippable.

`patterns.md` gained four findings in 0.5.1 when `LEAD_STRIP` took `|`. Before
that, `scan_line()` stripped a sentence with a set that omitted the pipe, so a
specimen quoted in the first cell of a Markdown table row kept its leading `| `
and every anchored `opener-*` rule missed it. Four of the catalog's own opener
specimens sat in that position and reported nothing. `bad-samples.md` carries
one table-position row per opener family to hold the path red-capable.

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
`dist/codex/grounded-copy`. `codex /plugins` does the same interactively.
Review and trust the hook definition in `/hooks` after installation. Codex
holds plugin hooks pending review until the user trusts them. `SessionStart`
runs for startup, resume, clear, and compact sources; the compact run restores
the stored active policy before continuation. `UserPromptSubmit` adds the
turn reminder through its additional-context output.

Invoke the profile controller explicitly:

```text
$grounded-profile chat
$grounded-profile copy
$grounded-profile off
$grounded-profile status
```

`chat` injects the core policy, `copy` adds the marketing register, and `off`
returns empty lifecycle output. A successful change writes
`$CODEX_HOME/grounded-copy/profile` atomically and prints the status plus a
governing directive. The stored value survives restarts. `### Profile
lifecycle` above defines the relationship among preference, policy, reminder,
and governing directive.

**`AGENTS.md`.** Codex reads it from the repo root, which reaches a project
checkout with no install step:

```markdown
## Copy style (mandatory)

Read `.style/grounded-copy/SKILL.md` before producing any user-facing copy.
Run `python3 .style/grounded-copy/scripts/copy_lint.py <files>` and iterate
until it exits 0. Do not modify the linter.
```

A Codex plugin registers lifecycle hooks under `hooks/hooks.json`; this adapter
uses `PLUGIN_ROOT` for its commands and provides Windows and POSIX launchers.
Run `python scripts/build_codex_adapter.py --check` to verify the generated
inventory and
`python skills/grounded-copy/scripts/copy_lint.py README.md skills/grounded-copy/references/setup.md`
to
verify this documentation.

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
