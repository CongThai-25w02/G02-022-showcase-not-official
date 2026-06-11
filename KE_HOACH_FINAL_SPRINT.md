# Đánh giá & Kế hoạch final sprint — nhắm 45+/50 + thuyết phục giám khảo đầu tư

> Ngày review: 2026-06-10 · Thời gian còn lại: >1 tuần · Quyết định đã chốt: **Bảng A chạy bằng model free quota cao (flash-lite)**, không bật billing.

---

## 1. Đánh giá hiện trạng (theo rubric 5×10đ)

| Tiêu chí | Ước tính hiện tại | Sau khi làm P0–P1 | Vì sao mất điểm hôm nay |
|---|---|---|---|
| Product/Business | ~6 | **9** | Bảng A trống, 0 feedback thật, chưa có live URL + video |
| System Design | ~9 | **9–10** | Đã mạnh: LangGraph, invariants, oracle, 3 sơ đồ Mermaid |
| UX/UI | ~7.5 | **8–9** | UI tốt nhưng chưa có bằng chứng công khai (video/live) cho giám khảo xem |
| DevOps | ~8 | **9–10** | Docker + CI + LangSmith có; thiếu deploy live + xác nhận trace |
| Code Quality | ~8.5 | **9** | 72 test + ruff + type hints; giữ nguyên kỷ luật |
| **Tổng** | **~39** | **44–47** | |

### Trạng thái 10 deliverables
✅ Source, README, Architecture, Pitch deck, Journal, Worklog
⚠️ AI Logs (chưa xác nhận trace thật trên LangSmith) · Eval evidence (**Bảng A trống**)
❌ **Live URL** · **Video demo**

### Phát hiện khi soát repo (cần xử lý)
1. **`eval/results/metrics_gemini_multiseed.csv` toàn lỗi 429** (chỉ t02 seed1 chạy được) — đây là lý do Bảng A trống. Nguyên nhân: `gemini-flash-latest` → gemini-3.5-flash free tier chỉ ~20 req/ngày.
2. **`eval/scenarios/m*.json` chưa có trong repo** — report_v2 tham chiếu m01–m11 nhưng file chưa sinh/commit. Giám khảo clone về sẽ không thấy. → chạy `python eval/gen_move_tasks.py` và **commit luôn m*.json**.
3. `USER_FEEDBACK.md` còn nguyên `[điền]` — chính file investor review đã gọi đây là cờ đỏ (A5).
4. README còn thiếu MSSV của Nguyễn Đình Tiến Mạnh.
5. CSV cũ (metrics_gemini.csv 7 task, metrics_ablation.csv mock) vẫn nằm cạnh v2 — giữ được, nhưng report_v2 phải là nguồn duy nhất được trích dẫn (đã đúng hướng).

---

## 2. P0 — Việc chặn điểm (làm xong trong 2–3 ngày đầu)

| # | Việc | Cách làm | DoD | Ai / ~giờ |
|---|---|---|---|---|
| P0.1 | **Bảng A — eval agent thật** | `.env`: `MODEL_NAME=gemini-flash-lite-latest` (flash-lite free ~30 RPM, quota/ngày cao hơn flash nhiều lần — xem cap thật trong AI Studio > Rate limits). Sinh task: `python eval/gen_move_tasks.py` → `python eval/run_eval_v2.py --seeds 3`. ~11 task × 3 seed × ~6 call ≈ 200 call → chạy 1 buổi với pacing/backoff. | report_v2.md có **mean ± std, n=33 run**, ghi rõ model = flash-lite; không còn chữ "CHƯA CHẠY" | Thái, 3–4h |
| P0.2 | **Commit bộ task m*.json** | Sau P0.1, `git add eval/scenarios/m*.json` | Clone sạch → chạy lại được eval không cần sinh | Thái, 10' |
| P0.3 | **Deploy live URL** | Theo `DEPLOY_runbook.md` (Render). Lưu ý đặt `MODEL_NAME` + `GEMINI_API_KEY` trong env của Render | `/health` OK, Demo nhanh chạy trên điện thoại; URL dán vào README + slide 1 | Đạt, 1–2h |
| P0.4 | **Video demo ≤3'** | Quay theo `presentation/video_script.md`, dùng live URL (không localhost); quay SAU khi có số Bảng A để đọc số thật | Link YouTube unlisted trong README + form | Mạnh, 2–3h |
| P0.5 | **≥5 feedback thật** (≥2 phi kỹ thuật) | Gửi live URL + 3 câu hỏi trong `eval/USER_FEEDBACK.md`, ghi nguyên văn | Bảng điền đủ ≥5 dòng + phần tổng hợp | Cả đội, 1 ngày chờ |
| P0.6 | **Xác nhận LangSmith** | Chạy 1 lệnh "Chạy thật" → kiểm tra project `ai20k-162` có trace | Screenshot trace dán vào JOURNAL/WORKLOG | Đạt, 15' |
| P0.7 | MSSV Mạnh + rà README | Điền MSSV; mọi số trong README trỏ về report_v2 | Không còn `[điền]` trong repo nộp | Mạnh, 10' |

**Phòng hờ P0.1:** nếu flash-lite vẫn 429 giữa chừng → chạy `--seeds 1` trước cho đủ 11 task (n=11, ghi rõ), bổ sung seed 2–3 hôm sau. **Tuyệt đối không** trộn số mock vào Bảng A — giữ đúng kỷ luật đã viết trong report.

---

## 3. P1 — Tăng điểm (ngày 3–5)

1. **README "hero block"**: ngay đầu — 1 câu định vị + bảng 3 số Bảng A (success mean±std, infeasible_correct, latency/bước) + link Live URL + Video. Giám khảo chấm nhanh, 30 giây đầu phải thấy đủ bằng chứng.
2. **Cập nhật pitch deck bằng số thật** (slide metric + slide demo): số từ report_v2, ghi chú "n=33 run, oracle chấm độc lập, mô phỏng 2D · agent thật".
3. **Latency trung thực + hướng xử lý** (A6 trong `Dieu_chinh_du_an_AI20K162.md`): nêu tách "vòng lập kế hoạch (LLM, ~giây)" vs "vòng thực thi (không LLM, ms)" + 1 hướng giảm có số mục tiêu.
4. **UX 30'**: kiểm tra responsive trên điện thoại thật qua live URL, contrast dark mode, aria-label cho nút chính — đủ để chấm "accessibility có quan tâm".
5. **Dry-run demo day 2 lần**: 1 lần theo `presentation/QA_prep_demoday.md`; quy tắc demo: mở bằng **replay** (không thể fail), kết bằng **1 lệnh chạy thật** (rủi ro có kiểm soát).
6. **Máy B (Gazebo) — giai đoạn 1 ĐÃ XONG** → làm tiếp giai đoạn 2 theo `PLAN_may_B_gazebo.md` §11: eval ≥3 task trên Gazebo (Bảng C), parity trace 2D↔Gazebo, runbook + slide sim→real. Đây là bằng chứng B3(b) mạnh nhất cho góc đầu tư.

---

## 4. P2 — Góc "giám khảo muốn đầu tư" (ngày 5–7)

Nguyên tắc lấy từ `K:\AI20K\Dieu_chinh_du_an_AI20K162.md` + `Investor_OnePager_AuditableAgents.md` (đã viết rất đúng — giờ thực thi):

1. **MỘT câu định vị duy nhất** (B1), dùng y hệt ở README, slide mở đầu, one-pager:
   *"Lớp thực thi agent kiểm chứng được (grounded + trace + biết nói không) — chứng minh phương pháp trên robot kho mô phỏng, ra lệnh tiếng Việt."*
   Robot kho = POC minh họa, không phải công ty. Không kể 2 câu chuyện song song.
2. **Ask đúng giai đoạn**: không xin vốn cổ phần — xin **1 pilot có tài trợ** trên quy trình thật (WMS/điều phối có sẵn của đối tác) + mentor GTM. Slide cuối: phạm vi pilot hẹp + 3 KPI (% hành động grounded, % audit pass, % được duyệt lên production) + kế hoạch 90 ngày.
3. **Moat roadmap trung thực** (B4): thừa nhận moat hiện mỏng; moat tích lũy = bộ eval ca-khó độc quyền tăng theo thời gian + thư viện audit-rule theo ngành + tích hợp sâu. Một chỉ số đo được: số ca khó trong bộ eval theo tháng.
4. **Vũ khí mạnh nhất với giám khảo = sự trung thực có cấu trúc**: Bảng A/B tách bạch, oracle độc lập, dám ghi "CHƯA CHẠY" thay vì bịa. Kể câu chuyện pivot #163→162 (tự nhận "chưa phải agent") — đây là tín hiệu đội đáng đầu tư hơn mọi con số.
5. **Q&A killer cần thuộc lòng**: sim-to-real ("sản phẩm là lớp plan+audit cắm vào hệ số hóa sẵn, không bán robot"), latency ("planner mức nhiệm vụ, không phải control loop"), moat ("đi sớm đúng nỗi đau trust + vòng dữ liệu eval"), "0 vi phạm an toàn?" ("không khoe số đó — sim chặn cứng; số có nghĩa là safety_events_handled").

---

## 5. Lịch 7 ngày gợi ý

| Ngày | Việc |
|---|---|
| D1 | P0.1 Bảng A (flash-lite) + P0.2 commit m*.json + P0.6 LangSmith + P0.7 MSSV |
| D2 | P0.3 Deploy Render → gửi link thu feedback (P0.5 bắt đầu) |
| D3 | P0.4 Quay video với số thật + P1.1 README hero |
| D4 | P1.2 pitch deck số thật + P1.3 latency + P1.4 UX pass |
| D5 | P0.5 chốt ≥5 feedback + tổng hợp · P2.1–2.3 (định vị, ask, moat) |
| D6 | Dry-run demo day ×2 + Q&A; sửa theo phản hồi nội bộ |
| D7 | Verify cuối (mục 6) + nộp sớm, chừa buffer |

## 6. Verify cuối trước khi nộp
- [ ] `pytest -q` xanh · `ruff check src tests eval` xanh
- [ ] Clone sạch repo → `gen_move_tasks` không cần chạy vẫn có m*.json → `run_eval_v2.py` (Bảng B) chạy OK
- [ ] report_v2.md: Bảng A có n + mean±std + model ghi đúng; README/slide/one-pager trích **cùng một số**
- [ ] Live URL: `/health` OK, demo chạy trên điện thoại · Video mở được ở chế độ ẩn danh
- [ ] `.env` không bị commit · USER_FEEDBACK ≥5 dòng thật · LangSmith có trace
- [ ] Một câu định vị xuất hiện y hệt ở README + slide 1 + one-pager
