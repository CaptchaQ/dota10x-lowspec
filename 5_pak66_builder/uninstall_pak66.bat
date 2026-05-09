@echo off
setlocal
REM ============================================================
REM  uninstall_pak66.bat
REM  Removes the pak66_dir.vpk override file from the Dota 2
REM  install. Optionally also removes a .bak backup if present.
REM ============================================================

where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python 3 not found.
  exit /b 1
)

REM Use Python to find the install path - same logic as kill_particles_pak66.py
for /f "delims=" %%i in ('python -c "import sys, pathlib; sys.path.insert(0, r'%~dp0..\2_particle_killer'); from vpk_reader import find_dota_install; p = find_dota_install(); print(p if p else '')"') do set DOTA=%%i

if "%DOTA%"=="" (
  echo [ERROR] Could not auto-detect Dota 2. Edit this script or remove pak66_dir.vpk manually.
  exit /b 1
)

set TARGET=%DOTA%\game\dota\pak66_dir.vpk
set BACKUP=%DOTA%\game\dota\pak66_dir.vpk.bak

echo === dota10x_lowspec :: uninstall_pak66 ===
echo Dota 2 install: %DOTA%
echo.

if not exist "%TARGET%" (
  echo [INFO] %TARGET% does not exist - nothing to remove.
) else (
  echo Found: %TARGET%
  choice /C YN /M "Delete pak66_dir.vpk?"
  if errorlevel 2 (
    echo Aborted.
    exit /b 0
  )
  del /f /q "%TARGET%"
  echo Deleted: pak66_dir.vpk
)

if exist "%BACKUP%" (
  echo.
  echo Found backup: %BACKUP%
  choice /C YN /M "Also delete pak66_dir.vpk.bak?"
  if errorlevel 2 goto :done
  del /f /q "%BACKUP%"
  echo Deleted: pak66_dir.vpk.bak
)

:done
echo.
echo Done. Restart Dota 2 - all particles back to vanilla.
pause
