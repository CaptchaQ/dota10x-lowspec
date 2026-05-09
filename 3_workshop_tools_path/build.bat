@echo off
setlocal
REM ============================================================
REM  build.bat - calls Workshop Tools resourcecompiler.exe to
REM              compile content/dota_addons/lowspec/ into _c
REM              files under game/dota_addons/lowspec/.
REM ============================================================

if "%~1"=="" (
  set /p DOTA=Path to "...steamapps\common\dota 2 beta": 
) else (
  set DOTA=%~1
)

set RC=%DOTA%\game\bin\win64\resourcecompiler.exe
if not exist "%RC%" (
  echo [ERROR] resourcecompiler.exe not found.
  echo Make sure Dota 2 Workshop Tools is installed:
  echo   Steam -^> Library -^> Tools -^> Dota 2 Workshop Tools
  exit /b 1
)

set CONTENT=%DOTA%\content\dota_addons\lowspec
if not exist "%CONTENT%" (
  echo [ERROR] %CONTENT% missing - run copy_to_content.bat first.
  exit /b 1
)

echo Building lowspec addon...
"%RC%" -gameid 570 -addon lowspec -i "%CONTENT%\..."
echo.
echo Done. Compiled _c files are under:
echo   %DOTA%\game\dota_addons\lowspec\
pause
