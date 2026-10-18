@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo Execute Instalar.cmd primeiro.
  pause
  exit /b 1
)
start "DuckCapture" ".venv\Scripts\pythonw.exe" "run.pyw"
