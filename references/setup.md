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
| Does the Skills CLI deliver the plugin files? | Its `.source` manifest lists four files (`SKILL.md`, both references, `copy_lint.py`), and the install carries no `.git` directory, so `.claude-plugin/` and `hooks/` arrive by `git clone` or by a marketplace install |
| Which launcher works? | `sh "${CLAUDE_PLUGIN_ROOT}/hooks/run.sh"` runs in the hook shell; `run.cmd` covers a setup lacking `sh` |
| Does `${CLAUDE_PLUGIN_DATA}` resolve for `@skills-dir`? | Yes — `~/.claude/plugins/data/grounded-copy-skills-dir`. The flag still uses a fixed path (see below) |
| Command name | `/grounded-copy:grounded`; plain `/grounded` returns "Unknown command" |

The flag lives at `<config-dir>/grounded-copy/profile`, one fixed path across
every install method. A marketplace install copies the plugin into
`~/.claude/plugins/cache`, so its `${CLAUDE_PLUGIN_ROOT}` moves to a new
directory on each version; a plugin discovered in a skills directory is read in
place, so that root holds still. One fixed path keeps the two methods on the
same file, and it holds user state, which belongs somewhere the user can cat,
edit, and grep while debugging the switch.

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
| `SessionStart` (no matcher) | `hooks/grounded_activate.py` | the session policy, 4,384 bytes under `chat`, repeated after each compaction |
| `UserPromptSubmit` | `hooks/grounded_tracker.py` | the turn reminder, 218 bytes |

Both hooks are read-only. `### Profile lifecycle` below defines every term
above and names the one path that records a preference.
`### Measured recurring cost` gives the figures and the method.

`_policy.py` reads `SKILL.md` at runtime and emits five core sections: the
intro with its example pair, the banned move with its seven shapes, the
deletion test, positive forms, scope and precedence, and sourcing. Run
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
| `scripts/copy_lint.py` | the deterministic gate: patterns, severities, exit codes |
| `scripts/build_codex_adapter.py` | building the Codex adapter from the canonical files, and `--check` |

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
| `chat` | the intro with its example pair, the banned move with its seven shapes, the deletion test, positive forms, scope and precedence, and sourcing — 4,278 bytes of rules | one line naming `chat` |
| `copy` | the same, plus the marketing register and two closures covering translation and the linter's standing as a floor — 5,835 bytes | one line naming `copy` |
| `off` | none | none |

`--self-test` prints the current figures and fails when a payload passes its
budget. `### Measured recurring cost` records the method and the history.

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

UTF-8 bytes of each hook's stdout, measured 2026-07-31 on Claude Code 2.1.220,
Windows 11. `python hooks/grounded_activate.py --self-test` prints the current
policy and reminder figures.

| Payload | Before | After |
|---|---|---|
| `chat` session policy, per `SessionStart` | 6,616 | 4,384 |
| `copy` session policy, per `SessionStart` | 8,873 | 5,941 |
| turn reminder, per prompt | 363 | 218 |
| `chat` governing directive, per switch | 6,582 | 4,527 |
| `copy` governing directive, per switch | 8,839 | 6,084 |
| `SKILL.md`, loaded when the skill triggers | 12,544 | 9,789 |

One 60-turn `chat` session with one compaction and one profile switch:
6,616 × 2 + 363 × 60 + 6,582 = 41,594 bytes before, and
4,384 × 2 + 218 × 60 + 4,527 = 26,375 bytes after, a 36.6% reduction.

Every token figure in this repository is an estimate at bytes ÷ 4 and is
labelled as one. No token count here comes from a tokenizer.

**Where the reduction came from.** The trigger-phrase catalogs and the example
tables moved out of `SKILL.md` into `references/patterns.md`, which already
held a bad → good rewrite for every shape. `SKILL.md` keeps the rule and the
opener for each of the seven shapes; `## Trigger phrases by shape` in
`references/patterns.md` holds the complete lists, and `## 12. Positive forms`
holds the positive-term rewrites. No rule left the payload. Two loophole
closures were folded into the rules they restated: the quote-and-testimonial
closure into **Verbatim source material**, and the headline-and-CTA closure
into the scope sentence of `## Marketing register`. The turn reminder dropped
`Prefer established positive terms`, the one clause with no evidence row and a
session-start statement of its own in `## Positive forms`.

**Evidence for the boundary change.** Examples and trigger phrases now have one
home. The measured cost of the old arrangement was 2,055 bytes of chat payload
and 2,755 bytes of copy payload per session, repeated after every compaction,
for text that `references/patterns.md` already carried and that arrives again
whenever the skill loads.

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
add this marketplace from git rather than from a direct URL to the JSON file.

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

### Change classification

Each change this branch made against `main`, and what happened to it here.

| Branch change | Classification |
|---|---|
| `SessionStart` hook and session policy | retained, simplified — same mechanism, payload down 33.7% |
| `UserPromptSubmit` turn reminder | retained, simplified — the one clause with no evidence row removed, payload down 39.9% |
| `--set` and the governing directive | retained — self-contained, one code path, no ordering assumption |
| `_preference.py`, single writer, fixed path | retained |
| `_hook_io.py` transport split | retained — both entry points call both functions |
| `run.sh` / `run.cmd`, closed dispatch, exit codes, argument forwarding | retained |
| natural-language switch parser | reverted earlier on this branch; the seventeen-prompt invariant stays in `ReadOnlyHookTests` |
| core rules added to `SKILL.md` | retained as rules, simplified as payload — trigger catalogs and examples relocated |
| loophole closures | split — two folded into the rules they restated, four skill-only, two in the `copy` payload |
| self-test tolerance band | redone — a published budget with a floor and a ceiling per payload, and the turn reminder now measured |
| token figures in `README.md` and `references/setup.md` | redone — measured bytes, estimates labelled as estimates |
| README disguise count and repository tree | redone |
| plugin-root quoting | requires supporting evidence — unchanged, measurement below |
| Claude Code marketplace, Codex marketplace, Codex adapter | added |

### Unresolved host behavior

One question needs a measurement on a live host. It blocks nothing that ships.

**Plugin-root quoting.** `.claude-plugin/plugin.json` keeps
`sh "${CLAUDE_PLUGIN_ROOT}/hooks/run.sh"`. `### Shell-facing values` above holds
the three-step measurement and the two candidate mechanisms. A working state
tells them apart in neither direction, so the quoting holds until the
measurement runs.

Codex marketplace path precedence was the second question here. The measured
table in `### Distribution` above answers it: Codex reads
`.agents/plugins/marketplace.json` and leaves the legacy
`.claude-plugin/marketplace.json` unread.

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
| 2026-08-01 | appositive reversal, code-span object | running prose in a chat reply | A and B |
| 2026-08-01 | bare "rather than" contrast | running prose in a chat reply | A and B |

Counting method: record a row when a banned move reaches user-visible output
with a profile active, naming the move, the surface, and the layers running.

The first two rows landed inside fenced blocks, which is why the deferred spec
selects fences by language tag and keeps untagged fences in scope. Rows three
and four landed in running prose, so surface selection covers the reply body as
well.

Both new rows happened with the session policy and the turn reminder in
context, and both sentences fail the deletion test — deleting the negated half
loses no information — so the guidance layer already prohibited them. The
specification was uniform; compliance was the failure.

What the deterministic layer did with them, measured:

| Row | `copy_lint.py` result | Exit |
|---|---|---|
| 3, code-span object | `0 error(s), 0 warning(s)` | 0 |
| 4, bare "rather than" | `1 warning`, rule `bare-rather-than` | 0 |

Row three misses because `comma-not-appositive` matches
`,\s*not\s+(?:a|an|another|your)` and the object opens with a backtick. Row
four matches at WARN, and WARN leaves the process exit at zero, so the gate
reports PASS. Neither reply passed through a gate in any case: no `Stop` hook
runs, so chat replies reach the user unlinted. That is the Phase 1 boundary
these rows exist to price.

**Promoting every WARN to ERROR, measured.** Ten of the 54 shipped rules are
WARN. Reclassifying them makes `tests/good-samples.md` fail on two lines:

- `The guide is general information, not a substitute for legal advice.`
- `Invoices are billed monthly rather than per seat.`

Those two lines are the false-positive counterexamples `CONTRIBUTING.md`
requires, and they are the required-disclaimer and billing-fact cases that
`## The deletion test` rules in. A uniform ERROR ban trades a corpus that
defines allowed factual negation for a gate that still leaves chat replies
unscanned, so it buys nothing on rows three and four. The deferred `Stop` hook
covers both without that trade.

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
| code-span object | widen `comma-not-appositive` so a backtick, quote, or bracket may open the object, WARN | rule name reported for the row-three sentence |
| zh reversal reveal, connector present | new `zh-not-x-but-y`, ERROR: negation, bounded gap, comma, explicit connector | lines in `tests/bad-samples.md`, exit 1 |
| zh reversal reveal, connector absent | new `zh-not-x-is-y`, WARN: the same shape with the connector dropped | rule name reported |
| wrapped phrases | `scan_text()` gains a wrap-joined pass with line-offset mapping | see below |

The zh row has its sighting, measured 2026-08-01 against a 285-line corpus of
two machine-written Chinese articles: `copy_lint.py` returns 4 errors, every
one `zh-not-just` on the era-ending member of that list, while 17 lines carry
the reversal reveal and clear the gate. `zh-not-just` enumerates the
minimizing and era-ending families, and the negate-then-assert structure sits
outside both. `## Multilingual equivalents` in
`references/patterns.md` holds the forms and the sighting lines; the linter
has no pattern for them.

The two rows split on the connector, and the split is measured. Candidates run
against the 17 corpus lines and against 9 hand-written factual negations:

| Candidate | Corpus lines matched | Factual lines matched |
|---|---|---|
| comma, bounded gap, explicit connector | 10 of 17 | 0 of 9 |
| comma, bounded gap, connector optional | 14 of 17 | 2 of 9 |

The connector-required form earns ERROR on that evidence. Dropping the
connector reaches four more corpus lines, and it also matches a required risk
disclaimer and a conditional clause whose negation and assertion belong to
different sentences, so it earns WARN and goes through the deletion test. That
mirrors the English pairs already shipped: `rather-than-simply` at ERROR beside
`bare-rather-than` at WARN, and `not-x-but-y` beside `comma-not-appositive`.

False-positive requirement for both rows: plain negation in Chinese opens with
the same characters, so each pattern needs both halves present within a bounded
gap, and `tests/good-samples.md` needs a factual negated line per severity that
keeps passing.

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

Citation cost, measured 2026-08-01: `README.md` produces 15 errors and 4
warnings, `SKILL.md` 44 errors and 12 warnings, and `references/patterns.md`
110 errors and 14 warnings — every one a banned pattern quoted as the example
that defines it. `references/setup.md` holds at 0 errors and 1 warning, so
sighting quotes belong in `references/patterns.md` and this file names counts. `SKILL.md` ran at 69 errors and 16 warnings before the trigger
catalogs moved into `references/patterns.md`, which is where the counts moved
too. The deferred `prose_gate.py` demotes a quoted or backticked ERROR to WARN
in the technical profile for this reason.

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
loophole, where an agent "fixes" the gate instead of the copy.

## Layer summary

| Layer | Mechanism | Catches |
|---|---|---|
| SKILL.md rules | Probabilistic | Novel phrasings, cross-sentence contrast |
| `copy_lint.py` | Deterministic | 50+ enumerated patterns, 9 languages |
| Claude Code hook | Blocking | Anything written to disk in-session |
| CI + CODEOWNERS | Blocking | Every agent and human; linter tampering |
