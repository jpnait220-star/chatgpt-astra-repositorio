@echo off
setlocal
cd /d "%~dp0"
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -STA -ExecutionPolicy Bypass -File "%~dp0DuckPC.ps1"
if errorlevel 1 (
  echo.
  echo O DuckPC nao iniciou. Extraia o ZIP inteiro para uma pasta e tente novamente.
  echo Se a politica da sua organizacao bloqueou scripts, nao altere essa politica.
  pause
)
endlocal
