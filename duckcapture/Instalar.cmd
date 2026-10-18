@echo off
setlocal
cd /d "%~dp0"
echo.
echo DuckCapture - instalacao local gratuita
py -3.12 --version >nul 2>&1
if errorlevel 1 (
  echo Instale o Python 3.12 de 64 bits para Windows em https://www.python.org/downloads/release/python-31210/
  echo Marque a opcao de instalar o Python Launcher e execute este arquivo novamente.
  pause
  exit /b 1
)
py -3.12 -c "import struct,sys; sys.exit(0 if struct.calcsize('P') == 8 else 1)"
if errorlevel 1 (
  echo E necessario usar o Python de 64 bits.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  py -3.12 -m venv ".venv"
  if errorlevel 1 goto :erro
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :erro
".venv\Scripts\python.exe" scripts\install_ffmpeg.py
if errorlevel 1 goto :erro
echo.
echo Pronto! Abra Iniciar DuckCapture.cmd. Nao mova apenas o iniciador: mantenha a pasta inteira.
pause
exit /b 0
:erro
echo.
echo A instalacao nao terminou. Confira a mensagem acima.
echo Para FFmpeg manual, veja LEIA-ME.md. Nao e preciso pagar nem assinar o aplicativo.
pause
exit /b 1
