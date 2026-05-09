@echo off
setlocal
REM ============================================================
REM  kill_particles_pak66.bat
REM  Builds pak66_dir.vpk inside <dota>\game\dota_minify\ that
REM  overrides every preset-matched particle with Valve's null
REM  stub. The folder is only mounted by Dota 2 when Steam launch
REM  options contain "-language minify".
REM
REM  Why dota_<locale>/ instead of dota/: putting the override
REM  in a language overlay folder bypasses Steam's "verify
REM  integrity of game files" (which would delete a non-vanilla
REM  pak in dota/), and Source 2 mounts language overlays AFTER
REM  the base, so the override is guaranteed to win. This is the
REM  same approach dota2-minify uses.
REM
REM  After this script:
REM    1. Run set_launch_option.bat (or add "-language minify"
REM       manually in Steam -> Properties -> Launch Options).
REM    2. Restart Steam + Dota 2.
REM ============================================================

REM Default preset; pass as first arg to override:
REM    kill_particles_pak66.bat safe        (~19,700 particles)
REM    kill_particles_pak66.bat aggressive  (~30,400 particles)
REM    kill_particles_pak66.bat nuclear     (~39,400 particles)
REM    kill_particles_pak66.bat total       (~80,700 - all)
set PRESET=%1
if "%PRESET%"=="" set PRESET=total

where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python 3 not found. Install from https://www.python.org/downloads/
  exit /b 1
)

REM Make sure 'vpk' Python package is installed
python -c "import vpk" >nul 2>&1
if errorlevel 1 (
  echo [INFO] Installing required 'vpk' Python package...
  python -m pip install vpk
  if errorlevel 1 (
    echo [ERROR] Failed to install 'vpk' package. Run manually:  pip install vpk
    exit /b 1
  )
)

echo === dota10x_lowspec :: kill_particles_pak66 ===
echo Preset: %PRESET%
echo.
echo Step 1/2 - DRY RUN (will show what would be packed):
python "%~dp0kill_particles_pak66.py" --preset %PRESET% --dry-run
if errorlevel 1 exit /b 1
echo.
choice /C YN /M "Build pak66_dir.vpk and place it next to pak01_dir.vpk?"
if errorlevel 2 (
  echo Aborted.
  exit /b 0
)
echo.
echo Step 2/2 - BUILDING pak66_dir.vpk...
python "%~dp0kill_particles_pak66.py" --preset %PRESET%
echo.
echo Done. Restart Dota 2 for changes to take effect.
echo.
echo To revert: run uninstall_pak66.bat (or delete pak66_dir.vpk manually)
pause
