:<<'BATCH'
@rem Gemini CLI hook launcher for grounded_tracker.py.
@"%~dp0run.cmd" grounded_tracker.py
BATCH
exec sh "$1/hooks/run.sh" grounded_tracker.py #
