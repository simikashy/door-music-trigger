' Launches the trigger with no visible console window.
' Used by the Startup-folder shortcut and Task Scheduler.
' Assumes pythonw.exe is on PATH (it is, with a standard python.org install).
Dim shell, scriptDir
Set shell = CreateObject("WScript.Shell")
' Run from this script's own folder so config.ini / tokens.json resolve.
scriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = scriptDir
shell.Run "pythonw door_music_trigger.py", 0, False
