@echo off
rem Resolve a Python 3 interpreter once, then run the named hook script once.
rem
rem `python X.py || python3 X.py` re-runs the script whenever the first
rem interpreter exits nonzero for any reason, which on SessionStart emits the
rem ruleset twice. Probing first, running once, avoids that.
rem
rem Exit 0 when no interpreter resolves: a style hook never breaks a session.
rem
rem Usage: run.cmd <script-name> [args...]

setlocal enabledelayedexpansion
set "HOOKDIR=%~dp0"
set "SCRIPT=%~1"
if "%SCRIPT%"=="" exit /b 0

set "ARGS="
:collect
shift
if "%~1"=="" goto run
set "ARGS=!ARGS! "%~1""
goto collect

:run
for %%P in (python python3) do (
    %%P -c "import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)" >nul 2>&1
    if !errorlevel! equ 0 (
        %%P "%HOOKDIR%%SCRIPT%" !ARGS!
        exit /b 0
    )
)

exit /b 0
