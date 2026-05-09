@echo off
setlocal
REM ============================================================
REM  kill_particles.bat - Windows wrapper for kill_particles.py
REM ============================================================

REM Default preset; pass as arg to override:
REM    kill_particles.bat safe        (~19,700 particles - cosmetics only)
REM    kill_particles.bat aggressive  (~30,400 particles - + spell trails/fx)
REM    kill_particles.bat nuclear     (~39,400 particles - all but projectiles)
REM    kill_particles.bat total       (~80,700 particles - EVERY particle in VPK)
set PRESET=%1
if "%PRESET%"=="" set PRESET=safe

where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python 3 not found. Install from https://www.python.org/downloads/
  exit /b 1
)

echo === dota10x_lowspec :: kill_particles ===
echo Preset: %PRESET%
echo.
echo Step 1/2 - DRY RUN (no files written):
python "%~dp0kill_particles.py" --preset %PRESET% --dry-run
if errorlevel 1 exit /b 1
echo.
choice /C YN /M "Apply these overrides for real?"
if errorlevel 2 (
  echo Aborted.
  exit /b 0
)
echo.
echo Step 2/2 - APPLYING overrides...
python "%~dp0kill_particles.py" --preset %PRESET%
echo.
echo Done. Restart Dota 2 for changes to take effect.
pause
