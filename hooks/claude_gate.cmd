:<<'BATCH'
@rem Claude Code hook launcher for grounded_gate.py. The manifest dot-sources this
@rem file, and the shell that runs the hook decides which half applies.
@rem
@rem cmd.exe reads the first line as a label, then hands over to run.cmd
@rem below. A batch file that names another batch file without `call`
@rem transfers control and never returns, so cmd.exe stops before the
@rem shell half. PowerShell runs a dot-sourced .cmd file through cmd.exe.
@rem `call` would expand `%` a second time and mangle a root that holds one.
@rem
@rem bash, sh, and zsh read the first line as a no-op `:` fed by a here
@rem document that ends at the BATCH line, then exec run.sh. Git keeps this
@rem file CRLF; the here-document marker and the closing line both carry
@rem the carriage return, and the trailing `#` turns the last one into a
@rem comment.
@"%~dp0run.cmd" grounded_gate.py
BATCH
exec sh "$CLAUDE_PLUGIN_ROOT/hooks/run.sh" grounded_gate.py #
