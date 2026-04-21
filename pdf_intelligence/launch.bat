@echo off
REM Launch script for PDF Intelligence
set PYTHONPATH=%cd%
python -OO -B src\main.py
pause
