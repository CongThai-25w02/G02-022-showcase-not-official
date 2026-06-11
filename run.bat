@echo off
REM ===========================================================
REM  RoboPlanner (AI20K-162) - chay showcase web 1 cham
REM  Backend FastAPI tu serve frontend tai http://localhost:8000
REM ===========================================================
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [1/3] Tao moi truong ao .venv ...
  python -m venv .venv
  if errorlevel 1 (
    echo LOI: khong tao duoc venv. Cai Python 3.11 va tick "Add Python to PATH".
    pause
    exit /b 1
  )
)

if not exist ".venv\.deps_ok" (
  echo [2/3] Cai thu vien lan dau ^(~1-2 phut^) ...
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo LOI: cai requirements that bai. Kiem tra mang roi chay lai.
    pause
    exit /b 1
  )
  echo ok> ".venv\.deps_ok"
)

if not exist ".env" (
  echo [!] Chua co .env - Demo nhanh van chay, nhung Chay that ^(Gemini^) se loi.
  echo     Tao bang:  copy .env.example .env   roi dien GEMINI_API_KEY
)

echo [3/3] Khoi dong server, mo http://localhost:8000 ...
start "RoboPlanner server" ".venv\Scripts\python.exe" -m uvicorn src.main:app --port 8000
timeout /t 4 >nul
start "" http://localhost:8000
echo.
echo Server dang chay o cua so "RoboPlanner server". DONG cua so do de dung.
echo Neu trinh duyet bao chua ket noi, doi 1-2 giay roi bam Refresh.
pause
endlocal
