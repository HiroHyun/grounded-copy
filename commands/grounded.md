---
description: Show or switch the grounded prose profile
argument-hint: chat|copy|off
---

Run this, substituting the plugin's own hooks directory if it differs from the
default path:

```bash
python ~/.claude/skills/grounded-copy/hooks/grounded_tracker.py --set $ARGUMENTS
```

Report the one line it prints. With empty arguments, read
`~/.claude/grounded-copy/profile` and report the current value instead. Change
no other files.

The script owns every write to the flag, whether a hook run or this command
triggers it. A prompt starting with `/` is resolved as a slash command before
any `UserPromptSubmit` event, so the hook's own prompt parsing covers plain
words ("switch grounded to copy", "stop grounded prose") while this command
covers the slash path.

Profiles:

- `chat` — the technical register. Reversal, era-ending, competitor contrast,
  absence-as-benefit, bait openers, and the hype list stay banned. Imperative
  verbs and code terms pass.
- `copy` — the marketing register, matching `SKILL.md` exactly.
- `off` — the session-start block and the per-turn reminder both stop. The
  value persists across restarts until `chat` or `copy` replaces it.

The flag lives at `<config-dir>/grounded-copy/profile`, where config-dir is
`$CLAUDE_CONFIG_DIR` when set and `~/.claude` otherwise.
