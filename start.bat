@echo off
chcp 65001 >nul
title 搜韵网收录诗文出处循证系统 v2.0.0
echo ======================================================
echo  📜 搜韵网收录诗文出处循证系统 (souyun-index) v2.0.0
echo ======================================================
echo.
cd /d "%~dp0"
python src\server.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [提示] 服务已停止。
)
pause

