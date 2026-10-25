@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 goto :py
where python >nul 2>nul
if not errorlevel 1 goto :python
start "" "https://www.python.org/downloads/windows/"
echo Instale Python 3.10 ou mais novo com Tkinter e marque Add python.exe to PATH.
pause
exit /b 1
:py
set "DUCKAC_PY=py -3"
goto :run
:python
set "DUCKAC_PY=python"
:run
%DUCKAC_PY% -c "import sys, tkinter; sys.exit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 (
    echo E necessario Python 3.10 ou mais novo com Tkinter.
    pause
    exit /b 1
)
%DUCKAC_PY% duckac.py
set "DUCKAC_EXIT=%errorlevel%"
if not "%DUCKAC_EXIT%"=="0" pause
exit /b %DUCKAC_EXIT%
