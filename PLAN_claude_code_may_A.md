# Kế hoạch chạy Claude Code trên MÁY A — Final sprint (P0 + P1)

> Mục tiêu: dùng Claude Code thực thi các việc P0/P1 của `KE_HOACH_FINAL_SPRINT.md` trên máy A (Windows).
> Bảng A chạy bằng **Ollama local** (đã chốt; `.env` đã đặt `LLM_PROVIDER=ollama`, model `qwen2.5:7b`).
> Mỗi phiên = 1 lần mở Claude Code với prompt dán sẵn bên dưới. Làm tuần tự, commit sau mỗi phiên.

## Kỷ luật chung (áp dụng mọi phiên)

- Mở Claude Code tại thư mục repo; bắt đầu việc lớn bằng **plan mode** (`Shift+Tab`) để duyệt kế hoạch trước khi cho sửa code.
- Sau mỗi phiên: `pytest -q` + `ruff check src tests eval` xanh → commit với message rõ ràng. **Không bao giờ commit `.env`**.
- Số liệu chỉ lấy từ `eval/results/report_v2.md`. Không cho Claude Code "làm đẹp" số — thiếu thì ghi CHƯA CHẠY.

---

## Phiên 0 — Chuẩn bị máy (người làm tay, ~15', KHÔNG cần Claude Code)

```bat
ollama pull qwen2.5:7b
ollama serve                      :: để chạy ở cửa sổ riêng, giữ mở suốt phiên 1
.venv\Scripts\activate
pip install langchain-ollama
```

Kiểm tra: `curl http://localhost:11434/api/tags` thấy `qwen2.5:7b`. `.env` đã có `LLM_PROVIDER=ollama` (xem `RUN_local_ollama.md`).

---

## Phiên 1 — P0.1 + P0.2: Bảng A bằng Ollama local (~2–4h, phần lớn là máy chạy)

**Prompt dán vào Claude Code:**

```
Đọc RUN_local_ollama.md và eval/run_eval_v2.py. Ollama đang chạy ở localhost:11434 với qwen2.5:7b.
1. Smoke test: chạy `python eval/run_eval_v2.py --seeds 1` và theo dõi. Nếu agent lỗi
   (tool-calling, parse JSON, timeout), chẩn đoán và sửa tối thiểu — KHÔNG đổi logic chấm
   điểm oracle, KHÔNG đổi công thức metric.
2. Khi 11 task chạy sạch với 1 seed: chạy `--seeds 3` (n=33 run).
3. Kiểm tra eval/results/report_v2.md: Bảng A phải có mean ± std cho success_rate, SPL,
   valid_action_rate, abstention, LLM calls, replans, latency; tiêu đề ghi rõ Ollama:qwen2.5:7b.
4. git add eval/scenarios/m*.json eval/results/ và commit "eval: Bảng A agent thật (Ollama local, n=33)".
Lưu ý: timeout mỗi run là 120s — model local chậm thì báo tôi cân nhắc tăng timeout
hoặc đổi model nhỏ hơn, đừng tự giảm số task.
```

**DoD:** report_v2.md hết chữ "CHƯA CHẠY"; `metrics_v2_agent.csv` có 33 dòng; m*.json đã commit (clone sạch chạy lại được).

**Phòng hờ:** qwen2.5:7b yếu/máy chậm → chấp nhận n=11 (`--seeds 1`) trước, ghi rõ n; bổ sung seed sau. Nếu số quá thấp (<50%), giữ số thật + thêm 1 đoạn phân tích lỗi — trung thực là vũ khí chấm điểm (P2.4).

---

## Phiên 2 — P0.6 + P0.7: LangSmith + dọn README (~30')

**Prompt:**

```
1. Kiểm tra .env có LANGCHAIN_API_KEY thật chưa (đừng in key ra). Nếu có: chạy 1 lệnh agent
   qua API (POST /api/v1/run hoặc 1 task eval) rồi hướng dẫn tôi mở LangSmith project
   ai20k-162-agent xác nhận trace. Tôi sẽ tự chụp screenshot dán vào WORKLOG.md.
2. README.md: điền MSSV còn thiếu của Nguyễn Đình Tiến Mạnh (tôi sẽ đưa số), rà toàn bộ
   số liệu trong README/SPEC/PRD — mọi con số về agent phải trỏ về report_v2.md, không còn
   chỗ nào trích số cũ hay placeholder [điền].
3. Commit "docs: xác nhận LangSmith + rà số liệu về report_v2".
```

**DoD:** screenshot trace trong WORKLOG; không còn `[điền]` ngoài USER_FEEDBACK (phiên người làm).

---

## Phiên 3 — P0.3: Deploy live URL (~1–2h)

⚠️ **Cloud KHÔNG chạy được Ollama.** Trên Render phải đặt `LLM_PROVIDER=gemini` + `MODEL_NAME=gemini-flash-lite-latest` + `GEMINI_API_KEY` (nút "Chạy thật" trên web dùng cloud, quota flash-lite đủ cho demo lẻ); "Demo nhanh (phát lại)" không cần key.

**Prompt:**

```
Đọc DEPLOY_runbook.md. Chuẩn bị deploy Render:
1. Rà Dockerfile/docker-compose: app phải đọc PORT từ env, không hardcode 8000.
2. Liệt kê chính xác các biến env cần đặt trên Render (LLM_PROVIDER=gemini,
   MODEL_NAME=gemini-flash-lite-latest, GEMINI_API_KEY, LANGCHAIN_*, MAX_STEPS...) —
   xuất thành checklist để tôi dán vào dashboard.
3. Tôi tự bấm deploy và đưa URL. Sau đó: kiểm tra /health, /docs, demo replay qua URL đó.
4. Dán Live URL vào README (hero) + presentation/, commit.
```

**DoD:** `/health` OK từ điện thoại; URL nằm trong README + slide 1. Gửi URL cho đội thu feedback (P0.5 — việc của người, bắt đầu ngay sau phiên này).

---

## Phiên 4 — P1.1 + P1.2: README hero + pitch deck số thật (~1h)

**Prompt:**

```
Đọc eval/results/report_v2.md (số thật từ phiên 1) và KE_HOACH_FINAL_SPRINT.md mục P1.1, P2.1.
1. Viết "hero block" đầu README: 1 câu định vị (lấy nguyên văn từ KE_HOACH mục P2.1) +
   bảng 3-4 số Bảng A (success mean±std, SPL, infeasible_correct, latency) ghi rõ
   "n=33, Ollama qwen2.5:7b local, oracle độc lập" + link Live URL + Video (placeholder nếu chưa quay).
2. Cập nhật presentation/ slide metric + slide demo bằng đúng các số đó — cùng MỘT nguồn số.
3. Commit "docs: README hero + pitch deck số thật từ report_v2".
```

**DoD:** 30 giây đầu đọc README thấy đủ: định vị, số có n, live URL, video.

---

## Phiên 5 — P1.3 + P1.4: latency note + UX pass (~1–1.5h)

**Prompt:**

```
1. Thêm vào README + slide phần latency trung thực: tách "vòng lập kế hoạch (LLM, ~giây/bước)"
   vs "vòng thực thi sim (không LLM, ms)"; nêu 1 hướng giảm có số mục tiêu
   (vd: cache plan, batch tool-call). Số latency lấy từ report_v2.
2. UX pass frontend/: kiểm tra responsive viewport nhỏ (~380px), contrast dark mode,
   aria-label cho các nút chính (Chạy, Demo nhanh, Reset). Sửa nhỏ, không redesign.
3. Chạy lại demo replay xác nhận không vỡ. Commit "ux: accessibility pass + latency note".
```

---

## Phiên 6 (tùy chọn, nếu còn thời gian) — Refactor WorldBackend

Theo `PLAN_may_A_web2d.md` §3 (hiện CHƯA làm — chưa có `WorldBackend`/`WORLD_BACKEND` trong src). Chỉ làm khi P0–P1 xong hết, vì rủi ro chạm code lõi sát deadline.

**Prompt:**

```
Đọc PLAN_may_A_web2d.md mục 3. Plan mode trước, tôi duyệt rồi mới code:
tách Protocol WorldBackend, gói World hiện tại thành Sim2DBackend, thêm cờ
WORLD_BACKEND=sim2d vào config (mặc định sim2d). Ràng buộc cứng: refactor
KHÔNG đổi hành vi — toàn bộ test hiện có phải xanh nguyên trạng, eval Bảng B
chạy lại ra đúng 9/9 + 2/2.
```

---

## Việc KHÔNG giao Claude Code (người làm)

P0.4 quay video (sau phiên 4, đọc số thật); P0.5 thu ≥5 feedback thật qua Live URL; lấy/đặt API key; bấm deploy trên dashboard Render; chụp screenshot LangSmith.

## Verify cuối (trước khi nộp — chạy như phiên riêng)

**Prompt:**

```
Chạy checklist mục 6 của KE_HOACH_FINAL_SPRINT.md từng dòng: pytest, ruff, clone sạch
ra thư mục tạm rồi chạy eval Bảng B, đối chiếu mọi số README/slide/one-pager với
report_v2.md, xác nhận .env không nằm trong git, USER_FEEDBACK ≥5 dòng. Báo cáo
PASS/FAIL từng dòng, KHÔNG tự sửa gì ở bước này — chỉ báo.
```

## Lịch gợi ý (khớp lịch 7 ngày của KE_HOACH)

| Ngày | Phiên |
|---|---|
| D1 | Phiên 0 → 1 (Bảng A Ollama) → 2 |
| D2 | Phiên 3 (deploy) → gửi link thu feedback |
| D3 | Quay video (người) + Phiên 4 |
| D4 | Phiên 5 |
| D5–6 | Feedback, dry-run demo, (Phiên 6 nếu dư thời gian) |
| D7 | Verify cuối + nộp sớm |
