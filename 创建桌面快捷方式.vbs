' ========================================================
' 搜韵网收录诗文出处循证系统 · 一键创建桌面快捷方式
' ========================================================
Set WshShell = CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")
strCurrentDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

strShortcutPath = strDesktop & "\搜韵网收录诗文出处循证系统.lnk"
Set oShortcut = WshShell.CreateShortcut(strShortcutPath)

' 目标指向根目录启动脚本
oShortcut.TargetPath = strCurrentDir & "\启动系统.bat"
oShortcut.WorkingDirectory = strCurrentDir
oShortcut.WindowStyle = 1
oShortcut.Description = "搜韵网收录诗文出处循证系统 (古典文献溯源与汇评集释)"

' 设置系统古典图标
oShortcut.IconLocation = "shell32.dll, 23"

oShortcut.Save

MsgBox "桌面快捷方式已成功创建！" & vbCrLf & vbCrLf & _
       "快捷方式名称：搜韵网收录诗文出处循证系统" & vbCrLf & _
       "今后您直接在桌面双击此图标即可一键启动并自动打开浏览器。", _
       vbInformation, "搜韵出处循证系统"
