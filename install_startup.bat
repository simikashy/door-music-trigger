@echo off
REM Registers the trigger to run automatically at logon via Task Scheduler.
REM Run this ONCE, by double-clicking it, from the project folder.
REM Restarts hidden (no console window) and survives logoffs better than a
REM Startup-folder shortcut.

setlocal
set "HERE=%~dp0"
set "VBS=%HERE%start_hidden.vbs"

schtasks /Create ^
  /TN "DoorMusicTrigger" ^
  /TR "wscript.exe \"%VBS%\"" ^
  /SC ONLOGON ^
  /RL LIMITED ^
  /F

if %ERRORLEVEL%==0 (
  echo.
  echo Installed. It will start automatically next time you log in.
  echo To start it right now without rebooting, run:  schtasks /Run /TN DoorMusicTrigger
  echo To remove it later, run:                        schtasks /Delete /TN DoorMusicTrigger /F
) else (
  echo.
  echo Install failed. Try running this file as Administrator.
)
pause
