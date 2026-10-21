@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
title DuckCapture - Finalizar instalador

echo.
echo  ===============================================
echo    DUCKCAPTURE - FINALIZAR INSTALADOR
echo  ===============================================
echo.
echo  Usando os arquivos que JA FORAM compilados.
echo  Nao sera necessario recompilar ou baixar novamente.
echo.
set "PYEXE="
set "PYARGS="
if exist ".build\venv\Scripts\python.exe" set "PYEXE=%~dp0.build\venv\Scripts\python.exe"
if not defined PYEXE (
    where py >nul 2>nul
    if not errorlevel 1 (
       set "PYEXE=py"
       set "PYARGS=-3.12"
    )
)
if not defined PYEXE if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PYEXE=%LocalAppData%\Programs\Python\Python312\python.exe"
if not defined PYEXE goto :python_missing
"%PYEXE%" %PYARGS% "scripts\finalize_installer.py"
if errorlevel 1 goto :failed
if exist "installer_saida\DuckCapture-Setup-0.4.7.exe" explorer.exe "%~dp0installer_saida"
echo.
echo Sucesso! O instalador foi salvo em installer_saida.
pause
exit /b 0
:python_missing
echo Python 3.12 nao encontrado; mantenha a pasta .build da compilacao anterior.
:failed
echo.
echo A finalizacao falhou. Envie as ultimas linhas de erro-build.log.
pause
exit /b 1
