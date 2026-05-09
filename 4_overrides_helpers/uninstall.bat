@echo off
setlocal EnableDelayedExpansion
REM ============================================================
REM  uninstall.bat - removes every override file logged by the
REM                  particle-killer (or any prior install run).
REM
REM  Uses the log at <DOTA>\game\dota\_dota10x_overrides.txt
REM ============================================================

if "%~1"=="" goto :ask
set DOTA=%~1
goto :have_path

:ask
set /p DOTA=Path to "...steamapps\common\dota 2 beta": 

:have_path
set LOG=%DOTA%\game\dota\_dota10x_overrides.txt
if not exist "%LOG%" (
  echo [ERROR] Log file not found: %LOG%
  echo Nothing to uninstall, or it was already uninstalled.
  exit /b 1
)

echo Removing override files listed in %LOG%
set /a CNT=0
for /f "usebackq delims=" %%L in ("%LOG%") do (
  set TARGET=%DOTA%\game\dota\%%L
  if exist "!TARGET!" (
    del /Q "!TARGET!"
    set /a CNT+=1
  )
)
echo Deleted !CNT! files.
del /Q "%LOG%"
echo Done. Original VPK content will be used again next launch.
pause
