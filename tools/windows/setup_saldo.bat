@echo off
rem ============================================================================
rem  Saldo bootstrap - send THIS file to the operator via Telegram and have her
rem  double-click it. It does NOT touch the old (locked) copy under Documents:
rem  it clones a FRESH copy into C:\Saldo (outside OneDrive, so no file-lock
rem  failures), carries over her config, makes the Desktop icon, and runs the
rem  first update. After this she only ever uses the "Update Saldo" icon.
rem
rem  Delivery note: Telegram sends .bat as a file. On first run Windows may show
rem  "Windows protected your PC" -> click "More info" -> "Run anyway" (or right-
rem  click the file -> Properties -> Unblock before running).
rem ============================================================================
setlocal
title Saldo setup

set "DEST=C:\Saldo"
set "REPO=%DEST%\Saldo-engine"
set "OLD=%USERPROFILE%\Documents\Saldo\Saldo-engine"
set "URL=git@github.com:vindm/Saldo.git"

where git >nul 2>nul || (echo [!] Git not found. Install Git for Windows, then run this again. & pause & exit /b 1)
where py  >nul 2>nul && (set "PY=py -3") || (set "PY=python")

echo === Setting up Saldo at %REPO% (outside OneDrive) ===
echo.

if exist "%REPO%\.git" (
  echo A copy already exists at %REPO% - it will just be updated.
) else (
  if not exist "%DEST%" mkdir "%DEST%"
  echo Cloning a fresh copy - this can take a minute. You may be asked for your SSH key passphrase once.
  git clone "%URL%" "%REPO%" || (echo [!] Clone failed - check internet / GitHub access. & pause & exit /b 1)
)

rem Carry over the existing configuration (data.dir, locale) from the old folder.
if exist "%OLD%\config\instance.yaml" if not exist "%REPO%\config\instance.yaml" (
  copy /y "%OLD%\config\instance.yaml" "%REPO%\config\instance.yaml" >nul
  echo Copied your config\instance.yaml from the old Documents folder.
)
if not exist "%REPO%\config\instance.yaml" (
  echo.
  echo [!] No config\instance.yaml found yet. Open %REPO%\config, copy
  echo     instance.example.yaml to instance.yaml and set data.dir + locale,
  echo     then run the Desktop icon. Ask Dima if unsure.
  echo.
)

echo Creating the Desktop icon ...
powershell -NoProfile -ExecutionPolicy Bypass -File "%REPO%\tools\windows\install_shortcut.ps1"

echo.
echo Running the first update (pull + migrations + dashboards) ...
echo.
%PY% "%REPO%\tools\update.py" --no-pause

echo.
echo ============================================================================
echo  Done. From now on just use the Desktop icon to update.
echo  The old folder under Documents can be deleted later (after pausing OneDrive).
echo ============================================================================
pause
