@echo off
setlocal
REM ============================================================
REM  set_launch_option.bat
REM  Adds (or removes) "-language <locale>" to the Dota 2 Steam
REM  launch options for every Steam account that has Dota 2 data.
REM
REM  Default locale: "minify" (matches the default --locale used
REM  by apply_mods.py / kill_particles_pak66.py).
REM
REM  Usage:
REM      set_launch_option.bat                          (-language minify)
REM      set_launch_option.bat --locale russian         (-language russian)
REM      set_launch_option.bat --locale minify --remove (remove it)
REM      set_launch_option.bat --dry-run                (preview only)
REM
REM  IMPORTANT: Steam MUST be closed for the edit to stick.
REM             Steam rewrites localconfig.vdf on exit.
REM ============================================================

where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python 3 not found. Install from https://www.python.org/downloads/
  exit /b 1
)

REM Make sure 'vdf' Python package is installed
python -c "import vdf" >nul 2>&1
if errorlevel 1 (
  echo [INFO] Installing required 'vdf' Python package...
  python -m pip install vdf
  if errorlevel 1 (
    echo [ERROR] Failed to install 'vdf' package. Run manually:  pip install vdf
    exit /b 1
  )
)

echo === dota10x_lowspec :: set_launch_option ===
echo.
echo IMPORTANT: Steam must be CLOSED for the change to stick (Steam
echo            rewrites localconfig.vdf on exit). Close Steam now,
echo            then press any key to continue.
pause >nul

python "%~dp0set_launch_option.py" %*
if errorlevel 1 (
  echo.
  echo [!] set_launch_option.py exited with non-zero code.
  pause
  exit /b 1
)

echo.
echo Done. Now relaunch Steam and start Dota 2.
pause
