@echo off
rem Run the named Antigravity hook once with python or python3.
setlocal
set "HOOKDIR=%~dp0"

set "SCRIPT="
if /i "%~1"=="grounded_activate.py" set "SCRIPT=grounded_activate.py"
if /i "%~1"=="grounded_tracker.py" set "SCRIPT=grounded_tracker.py"
if /i "%~1"=="grounded_gate.py" set "SCRIPT=grounded_gate.py"
if not defined SCRIPT (
    echo {}
    exit /b 0
)

python "%HOOKDIR%%SCRIPT%" %2 %3 %4 %5 %6 %7 %8 %9
if not errorlevel 9009 exit /b %ERRORLEVEL%
python3 "%HOOKDIR%%SCRIPT%" %2 %3 %4 %5 %6 %7 %8 %9
if not errorlevel 9009 exit /b %ERRORLEVEL%
if /i "%SCRIPT%"=="grounded_gate.py" (
    echo {"decision":"allow"}
) else (
    echo {}
)
exit /b 0
