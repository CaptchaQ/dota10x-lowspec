@echo off
setlocal
REM ============================================================
REM  strip_assets_pak66.bat
REM  Stubs out heavy asset categories (voice lines, music, attack
REM  sounds, cosmetic models, ...) into <dota>\game\dota_minify\
REM  pak66_dir.vpk to dramatically cut Dota 2's map load time.
REM
REM  Companion to kill_particles_pak66.bat - same dota_<locale>/
REM  + "-language <locale>" mechanism, just operates on
REM  non-particle file types.
REM
REM  Usage:
REM    strip_assets_pak66.bat                    (default: all-safe, ~7 GB stubbed)
REM    strip_assets_pak66.bat all-safe
REM    strip_assets_pak66.bat vo                 (just hero voice lines, ~3.7 GB)
REM    strip_assets_pak66.bat vo,music           (multiple categories, no spaces)
REM    strip_assets_pak66.bat all-safe --merge   (extend existing pak66)
REM    strip_assets_pak66.bat --list             (show all categories)
REM
REM  After this script:
REM    1. Run set_launch_option.bat (or add "-language minify"
REM       manually in Steam -> Properties -> Launch Options).
REM    2. Restart Steam + Dota 2.
REM ============================================================

set CATEGORIES=%1
if "%CATEGORIES%"=="" set CATEGORIES=all-safe
shift
set EXTRA=%1 %2 %3 %4 %5 %6 %7 %8 %9

where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python 3 not found. Install from https://www.python.org/downloads/
  exit /b 1
)

python -c "import vpk" >nul 2>&1
if errorlevel 1 (
  echo [INFO] Installing required 'vpk' Python package...
  python -m pip install vpk
  if errorlevel 1 (
    echo [ERROR] Failed to install 'vpk' package. Run manually:  pip install vpk
    exit /b 1
  )
)

if /I "%CATEGORIES%"=="--list" (
  python "%~dp0strip_assets_pak66.py" --list
  exit /b 0
)

echo === dota10x_lowspec :: strip_assets_pak66 ===
echo Categories: %CATEGORIES%
echo.
echo Step 1/2 - DRY RUN (will show what would be packed):
python "%~dp0strip_assets_pak66.py" --categories %CATEGORIES% --dry-run %EXTRA%
if errorlevel 1 exit /b 1
echo.
choice /C YN /M "Build pak66_dir.vpk in dota_minify\ ?"
if errorlevel 2 (
  echo Aborted.
  exit /b 0
)
echo.
echo Step 2/2 - BUILDING pak66_dir.vpk...
python "%~dp0strip_assets_pak66.py" --categories %CATEGORIES% %EXTRA%
echo.
echo Done. Restart Dota 2 for changes to take effect.
echo.
echo To revert: run uninstall_pak66.bat (or delete dota_minify\ manually)
pause
