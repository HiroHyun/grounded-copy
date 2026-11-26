---
name: grounded-profile
description: Show or change the grounded-copy writing mode when the user asks for chat, copy, off, or status.
---

# grounded-profile

Use this skill when the user explicitly asks to view or change the grounded-copy writing mode.

Run `python scripts/profile.py <operation>` (or `python3` if `python` is unavailable) from this skill directory. Accept exactly `chat`, `copy`, `off`, or `status` as the operation.

`chat` covers everyday interaction and ordinary document processing. `copy` is for product pages, marketing copy, and similar text. `off` stops the rules and reminders. `status` shows the saved setting.

The setting is saved at `$ANTIGRAVITY_CONFIG_DIR/grounded-copy/profile`, using `~/.gemini/config` as the default directory. After a successful change, report the status and apply the printed instructions from this turn forward. If saving fails, report the error.
