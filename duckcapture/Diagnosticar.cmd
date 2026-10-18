@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Execute Instalar.cmd primeiro.
  pause
  exit /b 1
)
echo DuckCapture - iniciando com console de diagnostico
".venv\Scripts\python.exe" -m duckcapture
pause
