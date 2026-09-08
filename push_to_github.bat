@echo off
setlocal
cd /d "%~dp0"
echo ========================================================
echo   Pushing souyun-index v2.0.0 to GitHub...
echo ========================================================
echo.
echo [1/2] Pushing branch: main ...
git push origin main
if errorlevel 1 (
    echo.
    echo [ERROR] Push main branch failed. Please authenticate if prompted.
    pause
    exit /b 1
)

echo.
echo [2/2] Pushing tag: v2.0.0 ...
git push origin v2.0.0 --force
if errorlevel 1 (
    echo.
    echo [ERROR] Push tag failed.
    pause
    exit /b 1
)

echo.
echo ========================================================
echo  [SUCCESS] Successfully pushed v2.0.0 to GitHub!
echo  Repository: https://github.com/ATP24/souyun-index
echo ========================================================
echo.
pause
