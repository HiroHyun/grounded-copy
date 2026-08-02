---
name: grounded-profile
description: Change or inspect the grounded-copy profile.
---

# grounded-profile

Use this skill only for an explicit profile operation. Invoke it as:

    $grounded-profile chat
    $grounded-profile copy
    $grounded-profile off
    $grounded-profile status

Run `python scripts/profile.py <operation>` from this skill directory. The
controller accepts exactly `chat`, `copy`, `off`, and `status`; it stores the
preference under `$CODEX_HOME/grounded-copy/profile`, prints status, and prints
the complete governing directive after a successful change.
