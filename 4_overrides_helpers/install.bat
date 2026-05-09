@echo off
setlocal
REM ============================================================
REM  install.bat - copies the prepared override pack into Dota 2
REM
REM  This script copies everything in:
REM      ..\..\override_pack\
REM  into:
REM      <DOTA>\game\dota\
REM
REM  Used after you've built your own _c files via Workshop Tools
REM  and dropped them into override_pack/.
REM
REM  For the simple particle-stub workflow, you should use
REM  2_particle_killer\kill_particles.bat instead - it writes
REM  directly into game/dota/.
REM ============================================================

if "%~1"=="" goto :ask
set DOTA=%~1
goto :have_path

:ask
set /p DOTA=Path to "...steamapps\common\dota 2 beta": 

:have_path
if not exist "%DOTA%\game\dota\pak01_dir.vpk" (
  echo [ERROR] %DOTA%\game\dota\pak01_dir.vpk not found.
  exit /b 1
)

set PACK=%~dp0..\override_pack
if not exist "%PACK%" (
  echo [ERROR] No override_pack folder found at %PACK%
  echo Build it first via 3_workshop_tools_path scripts, or use the particle-killer instead.
  exit /b 1
)

echo Copying overrides:
echo   FROM %PACK%
echo   TO   %DOTA%\game\dota
echo.
xcopy /E /I /Y "%PACK%\*" "%DOTA%\game\dota\"
echo.
echo Done. Launch Dota 2 to verify.
pause
