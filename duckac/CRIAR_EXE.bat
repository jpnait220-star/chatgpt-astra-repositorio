@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (set "DUCKAC_PY=py -3") else set "DUCKAC_PY=python"
%DUCKAC_PY% -c "import sys, tkinter; sys.exit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 goto :err
%DUCKAC_PY% -m pip install "pyinstaller>=6,<7"
if errorlevel 1 goto :err
%DUCKAC_PY% -m PyInstaller --noconfirm --clean --onefile --windowed --name DuckAC_V9_1 --icon assets\duckac.ico --add-data "assets;assets" duckac.py
if errorlevel 1 goto :err
echo.
echo PRONTO: dist\DuckAC_V9_1.exe
start "" "%~dp0dist"
pause
exit /b 0
:err
echo Falhou a criacao do EXE. Confira Python 3.10 ou mais novo, Tkinter e a conexao.
pause
exit /b 1
