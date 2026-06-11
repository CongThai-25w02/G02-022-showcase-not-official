# Deploy Runbook — AI20K‑162 (live URL trong ~10 phút)

> Mục tiêu: có **link công khai** để BTC mở được, kèm chế độ **Demo nhanh (phát lại)** chạy chắc 100%.
> Yêu cầu trước: đã làm **Phase 6** (StaticFiles + render.yaml + replay) · repo đã push GitHub · có **Gemini API key** + **LangSmith API key**.

## A. Chuẩn bị (1 lần)
1. **Gemini key:** Google AI Studio → Get API key (dạng `AIza…`).
2. **LangSmith key (AI logs):** smith.langchain.com → Settings → API key. Đặt project tên `ai20k-162`.
3. Đảm bảo **KHÔNG commit** `.env` (đã trong `.gitignore`); key chỉ điền ở dashboard Render.

## B. Deploy lên Render (Docker)
1. render.com → **New +** → **Web Service** → kết nối **GitHub repo** `C2-App-022`.
2. Runtime: **Docker** (Render tự đọc `Dockerfile`/`render.yaml`). Region: Singapore. Plan: Free.
3. **Environment → Add** các biến (Secret):
   | Key | Value |
   |---|---|
   | `GEMINI_API_KEY` | `AIza…` |
   | `GEMINI_MODEL` | `gemini-flash-latest` |
   | `LANGCHAIN_TRACING_V2` | `true` |
   | `LANGCHAIN_API_KEY` | `ls__…` |
   | `LANGCHAIN_PROJECT` | `ai20k-162` |
4. **Create Web Service** → chờ build (~3–5 phút).
5. Có URL dạng `https://ai20k-162.onrender.com`.

## C. Kiểm tra sau deploy
- [ ] Mở `…/health` → `{"ok": true}`.
- [ ] Mở `/` → thấy app + kịch bản hero tự nạp.
- [ ] Bấm **▶ Demo nhanh (phát lại)** → robot chạy + replan tức thì (không cần quota).
- [ ] Bấm **Chạy thật (Gemini)** 1 lần → agent chạy live (chậm ~30–60s là bình thường).
- [ ] Rút mạng/hết quota thử → hiện thông báo + gợi ý phát lại, **không crash**.

## D. Cập nhật sau khi có URL
- [ ] Dán URL vào **README** (dòng trạng thái) + **slide 1 pitch** + form nộp BTC.
- [ ] Tạo **QR** từ URL để chiếu lúc demo.

## E. Lưu ý ngày demo (chống "bể")
- Render Free **ngủ sau 15 phút** → lần mở đầu chờ ~30s "wake". **Mở trước 5 phút** cho nóng máy.
- Trên sân khấu: **mặc định bấm Demo nhanh** (chắc 100%), rồi mới bấm Chạy thật nếu mạng ổn.
- Backup: video 3 phút + chạy local `uvicorn src.main:app` trên laptop (đề phòng Render lỗi).

## Phương án thay thế
- **Railway** / **Fly.io**: tương tự, đọc Dockerfile, set cùng bộ env.
- Nếu chỉ cần frontend tĩnh phát lại (không agent live) → có thể bỏ lên **Vercel/Netlify** cho nhẹ, nhưng mất nút "Chạy thật".
