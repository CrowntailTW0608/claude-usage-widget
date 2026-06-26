Set sh = CreateObject("WScript.Shell")
Dim dir : dir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
sh.Run """" & dir & "\.venv\Scripts\pythonw.exe"" """ & dir & "\claude_usage_gui.py""", 0, False
Set sh = Nothing
