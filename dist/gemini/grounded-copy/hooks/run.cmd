@echo off
rem Run the named hook script once, with `python`, or with `python3` when
rem `python` did not start.
rem
rem `python X.py || python3 X.py` re-runs the script whenever the first
rem interpreter exits nonzero for any reason, which on SessionStart emits the
rem session policy twice. Exit code 9009 is the one fallback: cmd returns it
rem for a missing command, and so does the Microsoft Store stub, so the script
rem never ran. Each hook fires per tool call, and a separate version probe
rem cost one more interpreter start, about 70 ms, every time.
rem
rem The first argument is matched against a closed set and a literal is
rem assigned on match, so the executed command line derives from this file.
rem %SCRIPT% is re-expanded into that line, which is why it holds a constant
rem here. An unknown name exits 0 with no output.
rem
rem Delayed expansion stays off, and the remaining arguments are forwarded as
rem the positional parameters cmd already parsed. Enabling it consumed `!`
rem inside an argument, so `co!py` reached the hook as `copy`. Rebuilding the
rem command line from %* re-tokenizes instead, and the `for /f "tokens=1*"`
rem form ends its string early on a quoted path such as --plugin-root
rem "C:\gc test". The ceiling is eight arguments after the script name; the
rem hook commands pass one.
rem
rem Each run hands the interpreter's exit code back to the caller, which
rem the `--set` path needs: 0 recorded, 1 persistence failure, 2 rejected
rem value.
rem
rem Exit 0 when no interpreter resolves: a style hook stays non-blocking.
rem
rem Usage: run.cmd grounded_activate.py|grounded_tracker.py|grounded_gate.py
rem        [args...]

setlocal
set "HOOKDIR=%~dp0"

set "SCRIPT="
if /i "%~1"=="grounded_activate.py" set "SCRIPT=grounded_activate.py"
if /i "%~1"=="grounded_tracker.py" set "SCRIPT=grounded_tracker.py"
if /i "%~1"=="grounded_gate.py" set "SCRIPT=grounded_gate.py"
if not defined SCRIPT exit /b 0

python "%HOOKDIR%%SCRIPT%" %2 %3 %4 %5 %6 %7 %8 %9
if not errorlevel 9009 exit /b %ERRORLEVEL%
python3 "%HOOKDIR%%SCRIPT%" %2 %3 %4 %5 %6 %7 %8 %9
if not errorlevel 9009 exit /b %ERRORLEVEL%
exit /b 0
