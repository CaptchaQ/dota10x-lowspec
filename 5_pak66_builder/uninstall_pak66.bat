@echo off
setlocal
REM ============================================================
REM  uninstall_pak66.bat
REM  Removes the dota_<locale>\ language overlay folder created
REM  by kill_particles_pak66.py / apply_mods.py and (optionally)
REM  drops the "-language <locale>" Steam launch option.
REM
REM  Default locale is "minify". Pass another as the first arg:
REM      uninstall_pak66.bat
REM      uninstall_pak66.bat russian
REM ============================================================

set LOCALE=%1
if "%LOCALE%"=="" set LOCALE=minify

where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python 3 not found.
  exit /b 1
)

echo === dota10x_lowspec :: uninstall_pak66 ===
echo Locale: %LOCALE%
echo.

REM Step 1: remove the dota_<locale>\ folder via kill_particles_pak66.py --uninstall
python "%~dp0kill_particles_pak66.py" --locale %LOCALE% --uninstall
if errorlevel 1 (
  echo [!] kill_particles_pak66.py --uninstall failed.
  pause
  exit /b 1
)

echo.
echo IMPORTANT: For Dota to stop loading the override, you must
echo also remove "-language %LOCALE%" from Steam launch options.
echo.
choice /C YN /M "Drop '-language %LOCALE%' from Steam launch options now?"
if errorlevel 2 goto :done

echo.
echo (Steam must be CLOSED for this to stick.)
pause
python "%~dp0set_launch_option.py" --locale %LOCALE% --remove
if errorlevel 1 (
  echo [!] set_launch_option.py --remove failed.
  pause
  exit /b 1
)

:done
echo.
echo Done. Restart Steam + Dota 2 - all particles back to vanilla.
pause
