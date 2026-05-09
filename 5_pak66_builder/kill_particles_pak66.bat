@echo off
setlocal
REM ============================================================
REM  kill_particles_pak66.bat
REM  Builds pak66_dir.vpk next to pak01_dir.vpk and overrides
REM  every preset-matched particle with Valve's null stub.
REM
REM  Why pak66: Source 2 mounts every pak*_dir.vpk in numerical
REM  order, so pak66 wins over pak01 for the same paths. This
REM  is the same approach the popular dota2-minify uses.
REM  Loose-file overrides sometimes don't take effect on user
REM  installations - this VPK approach bypasses that.
REM ============================================================

REM Default preset; pass as arg to override:
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
