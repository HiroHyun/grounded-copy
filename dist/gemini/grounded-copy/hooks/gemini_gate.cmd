:<<'BATCH'
@rem Gemini CLI hook launcher for grounded_gate.py.
@"%~dp0run.cmd" grounded_gate.py
BATCH
exec sh "$1/hooks/run.sh" grounded_gate.py #
