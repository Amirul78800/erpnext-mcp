@echo off
cd /d "%~dp0"
echo ==========================================================
echo  Pushing erpnext-mcp to GitHub
echo  Remote: https://github.com/Amirul78800/erpnext-mcp.git
echo  Branch: main
echo ==========================================================
git push -u origin main
echo.
pause
