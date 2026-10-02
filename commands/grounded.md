---
description: Show or change the grounded-copy writing mode
argument-hint: chat|copy|off
disable-model-invocation: true
---

Run one command below and report its output. Match the user's argument to `chat`, `copy`, or `off`. For an empty or unknown argument, run the status command. Limit the operation to the profile setting.

`chat`:

```bash
sh '${CLAUDE_PLUGIN_ROOT}/hooks/run.sh' grounded_tracker.py --set chat
```

`copy`:

```bash
sh '${CLAUDE_PLUGIN_ROOT}/hooks/run.sh' grounded_tracker.py --set copy
```

`off`:

```bash
sh '${CLAUDE_PLUGIN_ROOT}/hooks/run.sh' grounded_tracker.py --set off
```

Status:

```bash
sh '${CLAUDE_PLUGIN_ROOT}/hooks/run.sh' grounded_tracker.py --status
```

Use the selected command exactly as written. Keep user-supplied text out of the shell command. For an unknown argument, report the rejected value and the current profile. Leave the saved setting unchanged.

A successful change prints status and the instructions for the new profile. Those instructions apply from this turn forward and replace the earlier grounded-copy policy for the session.

For `--set`, exit code `0` means saved, `1` means saving failed, and `2` means the value was rejected. `--status` returns `0`.

If the plugin path still contains a literal dollar-brace placeholder, report that path substitution failed and stop.

On Windows without `sh`, run the matching PowerShell command. The `&` call operator starts the quoted launcher path:

```powershell
& '${CLAUDE_PLUGIN_ROOT}\hooks\run.cmd' grounded_tracker.py --set chat
& '${CLAUDE_PLUGIN_ROOT}\hooks\run.cmd' grounded_tracker.py --set copy
& '${CLAUDE_PLUGIN_ROOT}\hooks\run.cmd' grounded_tracker.py --set off
& '${CLAUDE_PLUGIN_ROOT}\hooks\run.cmd' grounded_tracker.py --status
```
