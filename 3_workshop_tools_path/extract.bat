@echo off
setlocal
REM ============================================================
REM  extract.bat - extracts heavy assets from pak01_dir.vpk for
REM                downscaling/stripping pipeline.
REM
REM Requirements:
REM   tools_bin\Source2Viewer-CLI.exe   (download from
REM     https://github.com/ValveResourceFormat/ValveResourceFormat/releases)
REM
REM Usage:
REM   extract.bat                                  (auto-detect Dota path)
REM   extract.bat "C:\Path\to\dota 2 beta"
REM ============================================================

set HERE=%~dp0
set CLI=%HERE%tools_bin\Source2Viewer-CLI.exe
if not exist "%CLI%" (
  echo [ERROR] %CLI% not found.
  echo Download Source2Viewer-CLI from:
  echo   https://github.com/ValveResourceFormat/ValveResourceFormat/releases
  echo and put Source2Viewer-CLI.exe + DLLs into:
  echo   %HERE%tools_bin\
  exit /b 1
)

if "%~1"=="" (
  REM Auto-detect from registry
  for /f "tokens=2*" %%A in ('reg query "HKCU\Software\Valve\Steam" /v "SteamPath" 2^>nul') do set STEAM=%%B
  if defined STEAM (
    set DOTA=!STEAM!\steamapps\common\dota 2 beta
  )
  if not defined DOTA (
    set /p DOTA=Path to "...steamapps\common\dota 2 beta": 
  )
) else (
  set DOTA=%~1
)

set VPK=%DOTA%\game\dota\pak01_dir.vpk
if not exist "%VPK%" (
  echo [ERROR] %VPK% not found
  exit /b 1
)

set OUT=%HERE%extracted
mkdir "%OUT%" 2>nul

echo === Extracting hero textures + materials ===
"%CLI%" --input "%VPK%" --output "%OUT%" --vpk_filepath "materials/models/heroes/" --vpk_decompile

echo === Extracting map terrain textures ===
"%CLI%" --input "%VPK%" --output "%OUT%" --vpk_filepath "materials/maps/" --vpk_decompile
"%CLI%" --input "%VPK%" --output "%OUT%" --vpk_filepath "materials/cliffs/" --vpk_decompile
"%CLI%" --input "%VPK%" --output "%OUT%" --vpk_filepath "materials/ground/" --vpk_decompile
"%CLI%" --input "%VPK%" --output "%OUT%" --vpk_filepath "materials/trees/" --vpk_decompile

echo === Extracting skybox ===
"%CLI%" --input "%VPK%" --output "%OUT%" --vpk_filepath "materials/skybox/" --vpk_decompile

echo === Extracting decals ===
"%CLI%" --input "%VPK%" --output "%OUT%" --vpk_filepath "materials/decals/" --vpk_decompile

echo.
echo Extraction done. Output in %OUT%
pause
