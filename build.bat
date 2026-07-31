@echo off
echo ==============================================
echo 开始打包编译 Windows 单文件可执行程序 (.exe)
echo 确保您已经安装了 PyInstaller: pip install pyinstaller
echo ==============================================
cd src
pyinstaller --noconfirm --onefile --windowed --add-data "index.html;." --name "souyun-index-windows" server.py
echo ==============================================
echo 编译完成！您的独立程序在 src\dist\souyun-index-windows.exe 中。
pause
