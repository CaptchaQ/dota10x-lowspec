@echo off
setlocal
REM ============================================================
REM  dota10x_gui.bat
REM  Launches the dota10x-lowspec mini-builder GUI.
REM
REM  - Picks Python via the standard `py -3` launcher (works on
REM    every Windows install that has Python 3 from python.org).
REM  - Falls back to plain `python` if `py` is unavailable.
REM  - Auto-installs `vpk` and `vdf` (needed by the underlying
REM    CLI scripts) on first run.
REM ============================================================

set SCRIPT=%~dp0dota10x_gui.py

where py >nul 2>&1
if not errorlevel 1 (
  set PY=py -3
) else (
  where python >nul 2>&1
  if errorlevel 1 (
    echo [ERROR] Python 3 not found. Install from https://www.python.org/downloads/
    pause
    exit /b 1
  )
  set PY=python
)

REM First-run dependency check (silent if already installed)
%PY% -c "import vpk, vdf" >nul 2>&1
if errorlevel 1 (
  echo [INFO] First run: installing required packages 'vpk' and 'vdf'...
  %PY% -m pip install vpk vdf
  if errorlevel 1 (
    echo [ERROR] Failed to install dependencies. Run manually:
    echo            %PY% -m pip install vpk vdf
    pause
    exit /b 1
  )
)

REM Launch GUI (no console window). pythonw.exe = py -3w
where pyw >nul 2>&1
if not errorlevel 1 (
  start "" pyw "%SCRIPT%"
) else (
  start "" pythonw "%SCRIPT%"
  if errorlevel 1 (
    REM Fallback: launch with console attached (so errors are visible)
    %PY% "%SCRIPT%"
  )
)
