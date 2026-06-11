# Weekly Journal — Team AI20K (App‑022)

> Ghi lại mỗi tuần: học được gì, khó khăn gì, quyết định gì, kế hoạch tiếp.
> _Bám lịch sử dự án thật — gồm cả bước ngoặt đổi đề tài. Đội chỉnh ngày/tên cho khớp._

---

## Week 1: 2026‑05‑30 → 2026‑06‑03 — Khám phá #163 + dựng demo thị giác

### Mục tiêu tuần này
- [x] Chốt hướng & dựng demo "AI chạy thật" cho robot nhà máy (ban đầu theo #163 — VLM scene understanding)

### Đã hoàn thành
- Demo thị giác chạy thật trong trình duyệt: COCO‑SSD + OWL‑ViT (open‑vocab) + Depth Anything + tracking + quyết định + tab "Thật vs Mô phỏng".
- Khảo sát SOTA 06/2026; tự đánh giá vòng 2 (liệt kê lỗi đúng/sai).

### Bài học
- Object detection/VLM là commodity → moat ở dữ liệu + tích hợp.
- **Minh bạch (thật vs mô phỏng)** là điểm tạo niềm tin — giữ làm văn hoá đội.

### Kế hoạch tuần sau
- [x] Sản phẩm hoá demo (PWA + VLM thật + accuracy) và đánh giá lại mức độ "là Agent"

---

## Week 2: 2026‑06‑04 → … — Sản phẩm hoá, review, và **bước ngoặt đổi đề tài**

### Mục tiêu tuần này
- [x] Đóng gói sản phẩm CV + realtime
- [x] **Đánh giá lại theo rubric BTC**: dự án có thực sự là *Agent* không?
- [x] Quyết định hướng đi & viết scoping cho đề tài mới

### Đã hoàn thành
- PWA + Cloudflare Worker (Gemini) + script accuracy + realtime open‑vocab (Web Worker) + review nội bộ + sửa P0→P3.
- **Phân tích trung thực:** bản CV là *module tri giác + 1 lời gọi VLM*, **chưa phải agent** (không có vòng reason→plan→act, không tool‑calling). Gọi nó là "agent" sẽ là tô vẽ.
- **Quyết định pivot:** đổi sang **AI20K‑162 (Lập kế hoạch tác vụ) gộp 161 (điều khiển bằng ngôn ngữ)** — đây là *agent đúng nghĩa*, demo trọn trên laptop (sim 2D), **tái dùng perception cũ làm tool**.
- Viết **scoping + kiến trúc agent + tool list + plan 2 tuần** (`PLAN_agent_taskplanner.md`).

### Khó khăn & Giải pháp
| Khó khăn | Giải pháp | Kết quả |
|----------|-----------|---------|
| Dự án CV không khớp yêu cầu "Agent" của rubric | Đánh giá trung thực + đổi sang đề tài planning (162) | Hướng đi rõ, hợp rubric |
| Không có phần cứng robot | Dựng **kho mô phỏng 2D** ở backend; agent là thật | Demo được trên laptop |
| Sợ phí công CV cũ | Biến perception thành **tool tri giác** của agent | Tái dùng, không bỏ |

### Bài học
- "Là agent" = phải có **vòng lập kế hoạch + gọi tool + quan sát + sửa**, không phải gắn nhãn.
- Dám **pivot dựa trên tự đánh giá trung thực** tốt hơn cố ép dự án cũ vào khung chấm.

### Kế hoạch tuần sau (Week 3 — build agent)
- [ ] Phase 0–1: `World` sim 2D + render + 9 tool (có pytest)
- [ ] Phase 2: LangGraph plan loop (Gemini function‑calling) + stream trace
- [ ] Phase 3: replan + an toàn (ask_human khi có người)

---

## Week 3: 2026‑06‑05 → … — Build agent: Phase 0 (sim world + render) ✅

### Mục tiêu tuần này
- [x] **Phase 0**: `World` sim 2D (grid + A*) + `WorldState` schema + API state + frontend canvas render
- [x] Phase 1: 9 tool thao tác World + pytest từng tool
- [x] Phase 2: LangGraph plan loop (Gemini function‑calling) + stream trace qua WebSocket
- [x] Phase 3: replan + an toàn (ask_human/wait khi có người)
- [x] Phase 4: nối UI ↔ agent (animation + panel kế hoạch/trace + badge)

### Đã hoàn thành (Phase 0 — 05/06)
- `src/services/world.py`: grid 16×10, A* (heuristic Manhattan), tránh obstacle/người, `from_scenario(path|dict)`, singleton `get/set_current_world`.
- `src/models/schemas.py`: `Cell/Entity/Zone/WorldState` (Pydantic v2) — round‑trip có test.
- API: `GET /api/v1/world`, `POST /api/v1/scenario?name=` (404 nếu thiếu); frontend mount static.
- `frontend/`: canvas render robot/objects/people/zones, chọn kịch bản, badge "thế giới mô phỏng · agent thật"; nút **Chạy** disabled (chờ Phase 2 — trung thực).
- `eval/scenarios/`: 2 kịch bản (basic + **blocked**: người đứng cạnh tường obstacle — dựng sẵn cho demo replan Phase 3).
- **Kiểm thử:** `pytest -q` → 27 passed, 1 warning (0.81s); `ruff` sạch. *(warning từ boilerplate `test_graph`, không phải code world.)*

### Bài học
- Đặt "sim có thẩm quyền" ở backend (`World` Python) ngay từ đầu → logic test thuần được; A* có unit test cho cả edge case (goal bị chặn / không có đường / start≡goal).
- Externalize kịch bản ra JSON → tái dùng cho cả demo lẫn eval (Phase 5), không phải sửa code.

### Cần quyết trước khi đi tiếp
- **LLM provider:** scaffold đang là OpenAI (`config.py`, `requirements` pin `langchain-openai`) nhưng PLAN chọn **Gemini** function‑calling → cần thống nhất trước **Phase 2** (Phase 1 chưa cần).
- **Người là vật cản tĩnh hay động:** hiện A* tránh luôn người; muốn demo "gặp người → dừng/hỏi/replan" thì `move_to` nên đi từng ô và **dừng khi ô kế có người** → quyết ngay ở **Phase 1**.

### Đã hoàn thành (Phase 1 + 2 — 05/06)
- **Phase 1:** `World` thêm mutation (`move_robot_to` đi từng ô & dừng ở người, `pick/drop`, `advance_tick`), tách `is_blocked_static`/`astar_static`, khớp nhãn chuẩn hoá; 9 tool function‑calling đọc observation thật.
- **Phase 2:** chuyển provider → **Gemini** (`gemini-2.0-flash`); LangGraph `parse_goal→perceive→plan→act→observe→summarize`; `POST /run` + `WS /ws` stream trace; cap `max_steps`.
- **Kiểm thử:** `pytest -q` → **46 passed**, ruff sạch.

### Bài học
- Tách blocker tĩnh/động từ Phase 1 trả công ngay: `move_to` dừng ở người → observe đặt `status="blocked"` → graph đã chừa nhánh replan cho Phase 3.
- parse/plan node tự bóc "code fence" của LLM + fallback → chịu được kiểu trả lời bọc markdown của Gemini.

### Đã hoàn thành (Phase 3 + 4 — 05/06)
- **Phase 3:** node `replan` + safety (`wait`/`ask_human` khi có người), người **động** theo tick, cap `replans`→`failed`; test `test_replan_safety.py` + `test_dynamic.py`.
- **Phase 4:** `frontend/app.js` nối **WebSocket `/ws`** → **animate** robot/người từng bước + panel **kế hoạch** + panel **trace** (node→tool→observation) + **badge** trạng thái; backend stream world theo bước.
- **Kiểm thử:** `pytest -q` → **65 passed**; `ruff` → All checks passed. **Lần đầu có demo nhìn được trên trình duyệt.**

### Bài học (Phase 3 + 4)
- Để `wait` có nghĩa thì người phải **động** — nếu A* lặng lẽ vòng tránh thì không còn gì để replan/demo.
- Tách "sim có thẩm quyền" ở backend trả công ở Phase 4: UI chỉ cần render snapshot theo bước, không nhân đôi logic.

---

## Week 4: 2026‑06‑06 — Eval THẬT · thu hẹp scope · showcase sản phẩm

### Mục tiêu tuần này
- [x] Đo **agent Gemini thật** (không chỉ mock) + ablation replan trên harness A* xác định (chưa chạy trên LLM agent)
- [x] **Thu hẹp** phạm vi vào lõi đã chứng minh; sửa bug t01
- [x] Showcase chắc ăn (Phase 6: replay) + đa năng lực + audit (Phase 7)
- [ ] Deploy live URL · video · thu feedback (đang làm)

### Đã hoàn thành
- **Phase 5/5b/5c:** harness 19 task → chạy **Gemini thật** → tách Bảng A (agent) vs B (mock); sửa metric an toàn (bỏ stub, đo từ trace); **ablation replan trên harness A\* xác định** (ON 19/19 vs OFF 12/19; chưa chạy trên LLM agent); fix bug t01 "done sớm"; headline = 5 nhóm lõi, `safe_behavior_rate` riêng.
- **Phase 6/7:** chế độ **Phát lại** (bản ghi thật, chống mất mạng/quota) + đa năng lực (giao/replan/an toàn/nói‑không) + nhãn **grounded** + **xuất audit log** + khối ứng dụng/lộ trình robot thật. `pytest` **72 passed**, ruff sạch.

### Bài học (quan trọng nhất tuần)
- **Đo agent thật > đánh bóng mock.** Con số 100% mock không chứng minh agent; số thật (core 100% trên 7 task lõi · tổng 87.5% n=8 + caveat) đáng tin hơn nhiều và không bị bóc.
- **Dám thu hẹp.** Cắt phần lỏng (safety/infeasible khỏi headline), chốt lõi replan đã chứng minh → câu chuyện gọn và vững.
- **Soi góc nhà đầu tư:** nhận ra robot **mô phỏng** chưa phải startup gọi vốn được (chưa robot thật, chưa traction, moat mỏng). **Quyết định:** giữ đúng **chủ đề BTC #162**; phần "agent kiểm chứng" (grounded + audit, không hallucinate) là giá trị thật → để dành làm *proof‑of‑method* cho câu chuyện đầu tư riêng, không trộn vào bài thi.

### Kế hoạch tiếp (trước nộp)
- [ ] Deploy live URL (Render) + xác nhận LangSmith có trace.
- [ ] Quay video 3' + thu ≥3 feedback (`eval/USER_FEEDBACK.md`).
- [ ] Điền MSSV Mạnh; rà `SUBMISSION_CHECKLIST.md` rồi nộp.

---

<!-- Tiếp tục cho Week 5… nếu có. Cập nhật ngày & tên thật. -->
