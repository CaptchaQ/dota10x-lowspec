@echo off
setlocal
REM ============================================================
REM  copy_to_content.bat - copies work/ into the Workshop Tools
REM  content addon directory.
REM ============================================================

if "%~1"=="" (
  set /p DOTA=Path to "...steamapps\common\dota 2 beta": 
) else (
  set DOTA=%~1
)
set HERE=%~dp0
set WORK=%HERE%work
set DEST=%DOTA%\content\dota_addons\lowspec

if not exist "%WORK%" (
  echo [ERROR] %WORK% does not exist. Run downscale_textures.py and strip_materials.py first.
  exit /b 1
)

mkdir "%DEST%" 2>nul
echo Copying %WORK% -> %DEST%
xcopy /E /I /Y "%WORK%\*" "%DEST%\"
echo Done.
pause
