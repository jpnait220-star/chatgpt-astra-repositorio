@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set "PYEXE="
set "PYARGS="
echo.
echo  ===============================================
echo     DUCKCAPTURE - GERADOR DE INSTALADOR
echo  ===============================================
echo.
where py >nul 2>nul
if not errorlevel 1 (
    py -3.12 -c "import struct,sys; sys.exit(0 if struct.calcsize('P')==8 else 1)" >nul 2>nul
    if not errorlevel 1 (
        set "PYEXE=py"
        set "PYARGS=-3.12"
    )
)
if not defined PYEXE if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PYEXE=%LocalAppData%\Programs\Python\Python312\python.exe"
if not defined PYEXE (
    echo Python 3.12 nao encontrado. Tentando instalar automaticamente pelo Windows...
    where winget >nul 2>nul
    if errorlevel 1 goto :no_python
    winget install --id Python.Python.3.12 -e --source winget --scope user --accept-package-agreements --accept-source-agreements
    if errorlevel 1 goto :no_python
    if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PYEXE=%LocalAppData%\Programs\Python\Python312\python.exe"
    if not defined PYEXE (
        set "PYEXE=py"
        set "PYARGS=-3.12"
    )
)
echo.
echo Preparando DuckCapture e instalador...
"%PYEXE%" %PYARGS% "scripts\build_windows.py"
if errorlevel 1 goto :failed
echo.
echo INSTALADOR GERADO COM SUCESSO!
echo Encontre o arquivo em: installer_saida
if exist "installer_saida\DuckCapture-Setup-0.4.7.exe" explorer.exe "%~dp0installer_saida"
pause
exit /b 0
:no_python
echo.
echo Nao foi possivel instalar Python automaticamente.
echo Instale Python 3.12 x64 pelo site oficial python.org e tente de novo.
goto :failed
:failed
echo.
echo Nao foi possivel concluir. Leia o erro acima ou o arquivo erro-build.log.
pause
exit /b 1
