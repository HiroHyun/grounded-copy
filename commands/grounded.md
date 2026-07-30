---
description: Show or switch the grounded prose profile
argument-hint: chat|copy|off
---

The `UserPromptSubmit` hook has already written the profile flag for this
invocation. Read the flag file and report the active profile in one line.
Change no files.

Profiles:

- `chat` — the technical register. Reversal, era-ending, competitor contrast,
  absence-as-benefit, bait openers, and the hype list stay banned. Imperative
  verbs and code terms pass.
- `copy` — the marketing register, matching `SKILL.md` exactly.
- `off` — the session-start block and the per-turn reminder both stop. The
  value persists across restarts until `/grounded chat` or `/grounded copy`
  replaces it.

The flag lives at `$CLAUDE_PLUGIN_DATA/profile`, or at
`~/.claude/grounded-copy/profile` when that variable holds no path.
