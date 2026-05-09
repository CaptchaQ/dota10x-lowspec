@echo off
setlocal
REM ============================================================
REM  collect_compiled.bat - copies compiled _c files from
REM    game/dota_addons/lowspec/  into  4_overrides_helpers/override_pack/
REM  so install.bat can deploy them.
REM ============================================================

if "%~1"=="" (
  set /p DOTA=Path to "...steamapps\common\dota 2 beta": 
) else (
  set DOTA=%~1
)
set HERE=%~dp0
set SRC=%DOTA%\game\dota_addons\lowspec
set DST=%HERE%..\override_pack
if not exist "%SRC%" (
  echo [ERROR] %SRC% missing - run build.bat first.
  exit /b 1
)
mkdir "%DST%" 2>nul
echo Copying compiled overrides...
xcopy /E /I /Y "%SRC%\*" "%DST%\"
echo.
echo Done. Now run 4_overrides_helpers\install.bat to deploy.
pause
