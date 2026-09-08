@echo off
chcp 65001 >nul
title 搜韵网收录诗文出处循证系统
echo ======================================================
echo  📜 搜韵网收录诗文出处循证系统 - 正在启动服务...
echo ======================================================
echo.
cd /d "%~dp0\src"
python server.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [提示] 检测到 Python 启动异常，尝试以独立程序启动...
    cd /d "%~dp0\souyun-index-windows"
    if exist "souyun-index-windows.exe" (
        start "" "souyun-index-windows.exe"
    )
)
pause

