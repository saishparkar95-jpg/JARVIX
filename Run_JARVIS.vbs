Set WshShell = CreateObject("WScript.Shell")
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
' Run using pythonw.exe in background with NO terminal/black console window
WshShell.CurrentDirectory = strPath
WshShell.Run """" & strPath & "\.venv\Scripts\pythonw.exe"" """ & strPath & "\main.py""", 0, False
