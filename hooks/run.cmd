@echo off
rem Resolve a Python 3 interpreter once, then run the named hook script once.
rem
rem `python X.py || python3 X.py` re-runs the script whenever the first
rem interpreter exits nonzero for any reason, which on SessionStart emits the
rem ruleset twice. Probing first, running once, avoids that.
rem
rem Delayed expansion stays off, and the arguments are forwarded as the
rem positional parameters cmd already parsed. Enabling it consumed `!` inside
rem an argument, so `co!py` reached the hook as `copy`. Rebuilding the command
rem line from %* re-tokenizes instead, and the `for /f "tokens=1*"` form ends
rem its string early on a quoted path such as --plugin-root "C:\gc test".
rem The ceiling is eight arguments after the script name; both hook commands
rem pass two.
rem
rem Exit 0 when no interpreter resolves: a style hook never breaks a session.
rem
rem Usage: run.cmd <script-name> [args...]

setlocal
set "HOOKDIR=%~dp0"
set "SCRIPT=%~1"
if "%SCRIPT%"=="" exit /b 0

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
exit /b 0
