@echo off
rem Resolve a Python 3 interpreter once, then run the named hook script once.
rem
rem `python X.py || python3 X.py` re-runs the script whenever the first
rem interpreter exits nonzero for any reason, which on SessionStart emits the
rem session policy twice. Probing first and running once avoids that.
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
rem The last line hands the interpreter's exit code back to the caller, which
rem the `--set` path needs: 0 recorded, 1 persistence failure, 2 rejected
rem value.
rem
rem Exit 0 when no interpreter resolves: a style hook stays non-blocking.
rem
rem Usage: run.cmd grounded_activate.py|grounded_tracker.py [args...]

setlocal
set "HOOKDIR=%~dp0"

set "SCRIPT="
if /i "%~1"=="grounded_activate.py" set "SCRIPT=grounded_activate.py"
if /i "%~1"=="grounded_tracker.py" set "SCRIPT=grounded_tracker.py"
if not defined SCRIPT exit /b 0

set "PY="
python -c "import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)" >nul 2>&1
if not errorlevel 1 set "PY=python"
if defined PY goto run

python3 -c "import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)" >nul 2>&1
if not errorlevel 1 set "PY=python3"
if defined PY goto run

exit /b 0

:run
%PY% "%HOOKDIR%%SCRIPT%" %2 %3 %4 %5 %6 %7 %8 %9
exit /b %ERRORLEVEL%
