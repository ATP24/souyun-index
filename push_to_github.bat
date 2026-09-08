@echo off
chcp 65001 >nul
title 搜韵网收录诗文出处循证系统 - GitHub 推送助手
echo ========================================================
echo   搜韵网收录诗文出处循证系统 v2.0.0 - GitHub 一键推送
echo ========================================================
echo.
echo [1/2] 正在推送 main 主分支至 origin (https://github.com/ATP24/souyun-index.git)...
git push origin main
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [提示] 如果首次推送弹出 GitHub 登录窗口，请在浏览器中完成点击授权即可。
    echo [错误] main 分支推送未完成，退出码：%ERRORLEVEL%
    echo.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2/2] 正在同步推送 v2.0.0 规范化版本标签...
git push origin v2.0.0 --force
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [错误] 标签推送失败，退出码：%ERRORLEVEL%
    echo.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ========================================================
echo [成功] v2.0.0 源码、全套规范文档及版本标签已成功推送到 GitHub！
echo 仓库地址: https://github.com/ATP24/souyun-index
echo ========================================================
echo.
pause
