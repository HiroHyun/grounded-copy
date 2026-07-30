---
description: Show or switch the grounded prose profile
argument-hint: chat|copy|off
disable-model-invocation: true
---

Run exactly this, then report the single line it prints and change no other
files:

```bash
sh "${CLAUDE_PLUGIN_ROOT}/hooks/run.sh" grounded_tracker.py --set "$ARGUMENTS"
```

With no argument it reports the current profile, the reason for it, and the
resolved flag path. With `chat`, `copy`, or `off` it records that profile and
reports the result. Any other value is rejected and the flag holds still.

If the command line still carries a literal `${CLAUDE_PLUGIN_ROOT}`, the
substitution failed: report that and stop. On a Windows setup where `sh` is
absent from PATH, run
`"${CLAUDE_PLUGIN_ROOT}/hooks/run.cmd" grounded_tracker.py --set "$ARGUMENTS"`
instead, matching the launcher swap in `references/setup.md`.

The script owns every write to the flag, whether a hook run or this command
triggers it. A prompt starting with `/` is resolved as a slash command before
any `UserPromptSubmit` event fires, so this command carries the slash path
while the hook parses whole-prompt instructions, among them "switch grounded
to copy" and the deactivation phrase in `references/setup.md`.

Profiles:

- `chat` — the session block carries the intro with its example pair, the
  banned move with its ten disguises and the repair, and the factual-negation
  test. Roughly 780 tokens per session and per compaction.
- `copy` — the same block plus four closures that govern marketing register:
  quotes and testimonials, headline and CTA scope, translation, and the
  linter's standing as a floor. Roughly 290 tokens more.
- `off` — the session block and the per-turn reminder both stop. The value
  persists across restarts until `chat` or `copy` replaces it.

The flag lives at `<config-dir>/grounded-copy/profile`, where config-dir is
`$CLAUDE_CONFIG_DIR` when set and `~/.claude` otherwise.
