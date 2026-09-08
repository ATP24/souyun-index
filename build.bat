@echo off
chcp 65001 >nul
echo ==============================================
echo 开始打包编译 Windows 单文件可执行程序 (.exe)
echo 确保您已经安装了 PyInstaller: pip install pyinstaller
echo ==============================================
cd /d "%~dp0\src"
pyinstaller --noconfirm --onefile --windowed --add-data "index.html;." --name "souyun-index-windows" server.py
if %ERRORLEVEL% EQU 0 (
    echo.
    echo [INFO] 正在同步到 releases\v2.0.0 目录...
    if not exist "%~dp0\releases\v2.0.0" mkdir "%~dp0\releases\v2.0.0"
    copy /y "%~dp0\src\dist\souyun-index-windows.exe" "%~dp0\releases\v2.0.0\souyun-index-windows.exe" >nul
    echo ==============================================
    echo 编译成功！最新可执行程序已输出至 releases\v2.0.0\souyun-index-windows.exe
    echo ==============================================
)
pause
