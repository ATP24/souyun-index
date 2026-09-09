@echo off
title 搜韵网收录诗文出处循证系统
cd /d "%~dp0"

echo ========================================================
echo        搜韵网收录诗文出处循证系统 · 正在启动
echo ========================================================
echo.

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [INFO] 检测到本地 Python 环境，正在启动服务...
    python src\server.py
    goto end
)

if exist "dist\souyun-index-windows.exe" (
    echo [INFO] 未检测到 Python，正在启动 Windows 免安装便携版...
    start "" "dist\souyun-index-windows.exe"
    goto end
)

echo [错误] 未检测到 Python 环境，亦未找到 dist\souyun-index-windows.exe。
pause

:end
