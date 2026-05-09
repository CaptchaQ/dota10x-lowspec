@echo off
REM ===================================================================
REM dota10x-lowspec :: apply_mods.bat
REM
REM Applies vendored dota2-minify mods into <dota>\game\dota\pak66_dir.vpk.
REM
REM Usage:
REM     apply_mods.bat                          (default: all mods)
REM     apply_mods.bat all
REM     apply_mods.bat "Misc Optimization,Dark Terrain"
REM     apply_mods.bat all --dry-run
REM     apply_mods.bat all --merge              (extend existing pak66)
REM     apply_mods.bat --list                   (show available mods)
REM
REM Requires Python 3.7+ and the 'vpk' package:
REM     pip install vpk
REM ===================================================================
setlocal
cd /d "%~dp0"

set "ARGS=%*"
if "%ARGS%"=="" set "ARGS=all"

REM If first token starts with "--" (e.g. "--list"), pass as-is.
echo %ARGS% | findstr /b "--" >nul
if %ERRORLEVEL%==0 (
    python apply_mods.py %ARGS%
) else (
    python apply_mods.py --mods %ARGS%
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] apply_mods.py exited with code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Done. Restart Dota 2 to apply.
pause
