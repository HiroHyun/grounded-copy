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

## Claude Code

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
