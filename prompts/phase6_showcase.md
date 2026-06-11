# Prompt cho Claude Code — PHASE 6 (Sản phẩm SHOWCASE: deploy + chế độ Phát lại)

> Dán vào Claude Code. Mục tiêu: biến app thành **sản phẩm showcase chắc ăn** — mở link là dùng được, demo không "bể" dù mạng yếu/quota hết, mà vẫn **trung thực** (agent thật + bản ghi thật).
> Bối cảnh: Phase 0–5c xong (agent Gemini 100% core, UI đã nối WS). Nhưng agent ~4.3s/bước, free-tier ~10 req/phút → live URL công khai cần lưới an toàn.

```
NHIỆM VỤ PHASE 6 — theo thứ tự:

0) FIX BẢNG B EVAL (đang rỗng): chạy lại `python eval/run_eval.py --llm mock` để section
   "B. Mock reference solver" hiện đủ 18 task (hiện đang "N=0 / 0%"). Đảm bảo cả Bảng A (gemini,
   có sẵn) và Bảng B (mock) cùng có số trong report.md. (Nếu writer ghi đè mất Bảng A khi chạy mock,
   sửa để GIỮ cả hai — đọc kết quả gemini đã lưu + mock, ghi 1 report đủ A và B.)

1) DEPLOY CONFIG (live URL — Deliverable #5):
   - FastAPI mount `frontend/` qua StaticFiles ở "/" (mở root là thấy app).
   - `render.yaml` (hoặc Railway) deploy 1 dịch vụ từ Dockerfile; `HEALTHCHECK`/route `/health`.
   - Env cần set ở dashboard (KHÔNG commit): `GEMINI_API_KEY`, `GEMINI_MODEL`,
     `LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT`.
   - `docker compose up` chạy local OK; `/health` trả ok.

2) CHẾ ĐỘ "PHÁT LẠI" (lưới an toàn, KHÔNG tốn quota) — phần quan trọng nhất:
   - Ghi lại **1–2 lần chạy THẬT thành công** của agent Gemini (kịch bản hero: pallet → người
     chắn → replan → giao) thành fixture JSON: **chuỗi sự kiện WS y hệt** lúc chạy thật
     (mỗi bước: node, last_action, world snapshot, status, plan, answer). Lưu vào
     `frontend/replays/hero_replan.json` (+ 1 cái nữa nếu muốn).
   - Frontend thêm nút **“▶ Demo nhanh (phát lại)”**: đọc fixture và **tái dùng đúng pipeline
     render/animation/trace** đang có (chạy từng event với delay ~300ms), KHÔNG gọi backend/LLM.
   - Nhãn trung thực ngay cạnh: *“Phát lại bản ghi THẬT của agent Gemini — không gọi lại API.”*
   - Giữ nút **“Chạy thật (Gemini)”** cho ai muốn xem live.

3) HERO SCENARIO + LANDING POLISH:
   - Khi mở app: tự nạp kịch bản hero (người chắn lối) + hiện **chip lệnh mẫu** bấm-1-nút:
     “đưa pallet A tới chuyền 3, tránh người”.
   - Header gọn: tên sản phẩm + 1 dòng mô tả + badge **“thế giới mô phỏng · agent thật”**.
   - 2 nút rõ ràng: [▶ Demo nhanh] (phát lại) và [Chạy thật (Gemini)]; dropdown chọn kịch bản.

4) CHỐNG "BỂ" KHI LIVE:
   - Nếu “Chạy thật” gặp lỗi/timeout/429 (hết quota) → hiện thông báo thân thiện
     (“Gemini đang bận/quá tải — bấm ▶ Demo nhanh để xem bản ghi thật”), KHÔNG văng lỗi.
   - Cold start Render (dịch vụ ngủ) → vẫn mở được; phát lại chạy ngay không cần backend nặng.

RÀNG BUỘC: không phá Phase 0–5c; pytest+ruff xanh; escape text vào innerHTML; không commit secret.
Replay là **bản ghi thật** (không bịa kết quả) — nhãn rõ để không hiểu nhầm là chạy live.

DoD PHASE 6:
- Mở app (local hoặc deployed) → **▶ Demo nhanh** phát lại hero run tức thì, mượt, không tốn quota.
- **Chạy thật (Gemini)** vẫn chạy; gặp 429/timeout → fallback thông báo + gợi ý phát lại, không crash.
- Hero scenario tự nạp; landing gọn; `/health` ok; `docker compose up` chạy.
- Bảng B eval hiện đủ 18 task (không còn 0%). pytest+ruff xanh.
- Xong DỪNG, báo: link local + ảnh/màn các nút + xác nhận replay + 429 handling.
```

---

> Sau phase này, đội chỉ cần **bấm deploy** (xem `DEPLOY_runbook.md`) → có live URL. Khi demo trực tiếp: mặc định bấm **Demo nhanh** (chắc 100%), rồi nếu mạng ổn mới bấm **Chạy thật** để chứng minh agent live.
