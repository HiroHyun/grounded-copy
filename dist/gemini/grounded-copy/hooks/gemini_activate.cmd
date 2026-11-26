:<<'BATCH'
@rem Gemini CLI hook launcher for grounded_activate.py.
@"%~dp0run.cmd" grounded_activate.py
BATCH
exec sh "$1/hooks/run.sh" grounded_activate.py #
