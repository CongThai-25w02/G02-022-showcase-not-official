@echo off
REM RoboPlanner - chi phat lai (Demo nhanh), khong can backend/deps
setlocal
cd /d "%~dp0frontend"
echo Showcase (chi Demo nhanh) tai http://localhost:5500 ...
start "RoboPlanner demo" python -m http.server 5500
timeout /t 3 >nul
start "" http://localhost:5500
echo.
echo Server tinh dang chay o cua so "RoboPlanner demo". DONG cua so do de dung.
pause
endlocal
