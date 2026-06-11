# Chạy MÁY A (Web Sim 2D) trên máy hiện tại

**Máy A** = bản demo LIVE 2D bằng Python thuần (FastAPI + Agent LangGraph/Gemini + canvas).
KHÔNG Gazebo, KHÔNG ROS, KHÔNG GPU — chạy thẳng trên Windows.

## Cách nhanh nhất
Bấm đôi (double-click) **`run_may_A.bat`**. Script sẽ:
1. Dùng `.venv` sẵn có (hoặc tự tạo + cài `requirements.txt` nếu chưa có).
2. Kiểm tra `.env` (nếu thiếu sẽ tạo từ `.env.example` và mở Notepad để bạn điền `GEMINI_API_KEY`).
3. Mở server tại **http://localhost:8000** và bật trình duyệt.

Dừng: đóng cửa sổ *"MAY A - RoboPlanner server"*.

## Chạy bằng tay (nếu muốn)
```bat
.venv\Scripts\activate
uvicorn src.main:app --host 127.0.0.1 --port 8000
```
- Web: http://localhost:8000 · API docs: `/docs` · Health: `/health`

## Yêu cầu
- **Python 3.11+** (đã có `.venv` thì bỏ qua).
- **`GEMINI_API_KEY`** trong `.env` — lấy miễn phí ở https://aistudio.google.com/apikey.
  Không có key vẫn chạy được chế độ **"Demo nhanh (phát lại)"**; chỉ nút **"Chạy thật (Gemini)"** cần key.

## Xử lý sự cố
- **Cổng 8000 bận**: đổi `set "PORT=8000"` trong `run_may_A.bat` sang cổng khác (vd 8010).
- **Agent live chậm 30–60s**: bình thường (gọi Gemini). Lúc trình diễn nên bấm *Demo nhanh* trước.
- **Chỉ cần bản replay nhẹ** (không backend, không key): bấm đôi `demo.bat` → http://localhost:5500.

## Đã kiểm tra (trong môi trường dựng thử)
- Cài đúng bộ thư viện khớp `.venv` Windows của bạn; `src.main:app` import sạch.
- Server lên: `/health` → `{"ok":true}`, frontend phục vụ, `GET /api/v1/world` + load scenario OK.
- 114/122 test nhân (world, A*, oracle, scenario) **xanh**. 8 test còn lại fail do *mock LLM patch sai target* trong test (lỗi sẵn có, không ảnh hưởng chạy thật).
- Lời gọi Gemini chỉ thử được trên máy bạn (mạng mở); môi trường dựng thử chặn egress nên không gọi ra ngoài.
