@echo off
REM ============================================================
REM  MAY A - RoboPlanner Web Sim 2D  (local / may hien tai)
REM  FastAPI + Agent (sim2d) tai http://localhost:8000
REM  Bam doi (double-click) de chay.
REM ============================================================
setlocal enableextensions
cd /d "%~dp0"

set "PORT=8000"
REM Co backend cho May A (Gazebo nam o May B). Config bo qua neu khong dung.
set "WORLD_BACKEND=sim2d"

REM --- 1) Python cua venv: uu tien .venv san co, neu thieu thi tao ---
set "VPY=.venv\Scripts\python.exe"
if not exist "%VPY%" (
  echo [setup] Khong thay .venv - dang tao moi...
  where py >nul 2>&1 && ( py -3.11 -m venv .venv 2>nul || py -3 -m venv .venv ) || python -m venv .venv
  if not exist "%VPY%" (
    echo [LOI] Khong tao duoc .venv. Hay cai Python 3.11+ roi chay lai.
    pause & exit /b 1
  )
  echo [setup] Cai dependencies (lan dau, ~1-3 phut)...
  "%VPY%" -m pip install --upgrade pip
  "%VPY%" -m pip install -r requirements.txt
  if errorlevel 1 ( echo [LOI] Cai dependencies that bai. & pause & exit /b 1 )
)

REM --- 2) Bao dam co .env chua GEMINI_API_KEY ---
if not exist ".env" (
  copy /y ".env.example" ".env" >nul
  echo.
  echo [CHU Y] Da tao .env tu .env.example.
  echo         Mo .env, dien GEMINI_API_KEY ^(lay mien phi tai
  echo         https://aistudio.google.com/apikey^) roi chay lai file nay.
  echo         * Khong co key van chay duoc che do "Demo nhanh (phat lai)".
  echo.
  notepad ".env"
  pause & exit /b 0
)

REM --- 3) Khoi dong server (cua so rieng) + mo trinh duyet ---
echo [run] Dang khoi dong MAY A tai http://localhost:%PORT% ...
start "MAY A - RoboPlanner server" "%VPY%" -m uvicorn src.main:app --host 127.0.0.1 --port %PORT%
timeout /t 5 >nul
start "" "http://localhost:%PORT%"
echo.
echo  Server dang chay o cua so "MAY A - RoboPlanner server".
echo  - Trang web:   http://localhost:%PORT%
echo  - API docs:    http://localhost:%PORT%/docs
echo  - Health:      http://localhost:%PORT%/health
echo  DONG cua so server do de dung May A.
echo.
pause
endlocal
