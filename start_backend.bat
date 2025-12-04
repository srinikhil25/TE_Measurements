@echo off
echo Starting TE Measurements Backend...
echo.
echo Using port 8080 (school network friendly)
echo.
uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
pause

