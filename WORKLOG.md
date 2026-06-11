# Worklog — Team AI20K (App‑022)

> Ghi lại tất cả công việc đã làm theo ngày. Ai làm gì, kết quả gì.
> _Bản nháp bám lịch sử thật — đội xác nhận lại tên người & số giờ._

---

## 2026‑05‑30 → 06‑03 — Khám phá #163 + demo thị giác

| Member | Task | Status | Output | Time |
|--------|------|--------|--------|------|
| Thái | Dựng demo CV (UI + COCO‑SSD + tabs) | ✅ Done | `AI20K_Demo_v3.html` | 8h |
| Đạt | Tích hợp OWL‑ViT (open‑vocab) + Depth | ✅ Done | engine open‑vocab/depth | 7h |
| Mạnh | Tracking + quyết định + tự đánh giá vòng 2 | ✅ Done | tab live + đánh giá | 6h |

**Tổng kết:** demo thị giác chạy thật; nhận ra cần đánh giá mức độ "là Agent".

---

## 2026‑06‑04 — Sản phẩm hoá + review + **pivot sang 162**

| Member | Task | Status | Output | Time |
|--------|------|--------|--------|------|
| Thái | PWA + đóng gói + realtime open‑vocab (Web Worker) | ✅ Done | `AI20K_Product/` | 5h |
| Đạt | Cloudflare Worker (Gemini) + fix review P0→P3 | ✅ Done | `vlm-proxy/` | 4h |
| Mạnh | Script accuracy + checklist demo | ✅ Done | `accuracy/` | 3h |
| Cả nhóm | **Đánh giá rubric → quyết định pivot 162** + viết scoping | ✅ Done | `PLAN_agent_taskplanner.md` | 3h |

**Tổng kết:** kết luận bản CV chưa "là agent" → **pivot sang AI20K‑162 (task‑planner agent)**; hoàn tất scoping + kiến trúc + plan 2 tuần.

---

## 2026‑06‑05 — Build agent Phase 0 (sim world + render) ✅

| Member | Task | Status | Output | Time |
|--------|------|--------|--------|------|
| Đạt | `src/services/world.py` (grid 16×10 + A* + `from_scenario`) + schema `Cell/Entity/Zone/WorldState` | ✅ Done | `world.py`, `schemas.py` | _đội xác nhận_ |
| Mạnh | Frontend canvas render world (robot/objects/people/zones) + ô nhập mục tiêu + chọn kịch bản | ✅ Done | `frontend/` | _đội xác nhận_ |
| Thái | API `GET /world` + `POST /scenario`, 2 kịch bản mẫu, pytest (world+api) + ruff | ✅ Done | `routes.py`, `eval/scenarios/*.json`, `tests/` | _đội xác nhận_ |

**Tổng kết:** `pytest -q` → **27 passed, 1 warning** (0.81s); `ruff check src tests` → **sạch**. DoD Phase 0 đạt: mở web thấy kho 2D, nạp được bản đồ mẫu (basic/blocked), robot đứng yên. _(1 warning đến từ boilerplate `test_graph`/langgraph, KHÔNG phải code world — sẽ thay ở Phase 2.)_

---

## 2026‑06‑05 — Build agent Phase 1 + 2 (tools + agent loop + Gemini) ✅

| Member | Task | Status | Output | Time |
|--------|------|--------|--------|------|
| Đạt | `World` mutation: `move_robot_to` (đi từng ô, dừng ở người), `pick/drop`, `advance_tick`; tách `is_blocked_static`/`astar_static`; khớp nhãn chuẩn hoá (NFC+casefold) | ✅ Done | `world.py` | _đội xác nhận_ |
| Thái | 9 tool function‑calling (`tools.py`) + chuyển provider → **Gemini** (`config/llm/requirements`) + LangGraph graph/nodes (parse_goal→perceive→plan→act→observe→summarize) | ✅ Done | `agents/`, `llm.py` | _đội xác nhận_ |
| Mạnh | API `POST /run` + `WS /ws` stream trace; pytest tools/graph/run | ✅ Done | `routes.py`, `tests/` | _đội xác nhận_ |

**Tổng kết:** `pytest -q` → **46 passed, 1 warning** (0.52s); `ruff check src tests` → **sạch**. DoD Phase 1 (tool đổi World thật, có test) + Phase 2 (mục tiêu tiếng Việt → agent tự lập kế hoạch + thực thi + trace) đạt. Cap `max_steps` chống treo; tool đọc observation thật (không hallucinate). Phase 3 đã có **móc nối sẵn**: `move_to` trả `blocked_by`, observe đặt `status="blocked"`, graph chừa nhánh route.

---

## 2026‑06‑05 — Build agent Phase 3 (replan + an toàn) ✅

| Member | Task | Status | Output | Time |
|--------|------|--------|--------|------|
| Đạt | Node `replan` + `safety` (ask_human/wait khi có người), đếm `replans` có cap, wire cap→`failed` | ✅ Done | `replan_node.py` | _đội xác nhận_ |
| Thái | Người động (lịch `dynamic` theo tick) để `wait` có tác dụng; 1 tool‑call/step; dọn boilerplate | ✅ Done | `world.py`, nodes | _đội xác nhận_ |
| Mạnh | Kịch bản + test replan/safety (`test_replan_safety.py`, `test_dynamic.py`) | ✅ Done | `tests/` | _đội xác nhận_ |

**Tổng kết:** người chắn lối → `move_to` trả `blocked_by` → observe đặt `status="blocked"` → node `replan` đổi đường; người sát robot → `wait`/`ask_human`. Cap `replans`→`failed` chống treo. `ruff` sạch.

---

## 2026‑06‑05 — Build agent Phase 4 (wire UI ↔ agent: animation + trace) ✅

| Member | Task | Status | Output | Time |
|--------|------|--------|--------|------|
| Mạnh | `frontend/app.js`: nối nút Chạy → WebSocket `/ws`, **animate** robot/người từng bước, panel kế hoạch + **trace** (node→tool→observation), **badge** trạng thái | ✅ Done | `frontend/` | _đội xác nhận_ |
| Đạt | Backend stream trạng thái world theo bước cho UI animate; giữ hợp đồng `/run`,`/ws` | ✅ Done | `routes.py` | _đội xác nhận_ |
| Thái | Test WS/route + giữ xanh; (stretch) voice tiếng Việt | ✅ Done | `tests/` | _đội xác nhận_ |

**Tổng kết:** `pytest -q` → **65 passed**; `ruff check` → **All checks passed**. Lần đầu **demo nhìn được trên trình duyệt**: gõ mục tiêu tiếng Việt → robot di chuyển từng bước + kế hoạch + trace + badge. *(Cần chạy thử tay 1 lần để xác nhận animation mượt + replan khi gặp người — theo DoD Phase 4.)*

---

## 2026‑06‑06 — Phase 5 + 5b + 5c (eval harness → eval THẬT → thu hẹp scope) ✅

| Member | Task | Status | Output |
|--------|------|--------|--------|
| Thái | Phase 5: 19 scenario JSON + `run_eval.py` (success/safety/ablation) + Docker/render config | ✅ Done | `eval/`, `render.yaml` |
| Đạt | Phase 5b: chạy **Gemini thật** → tách Bảng A (agent) vs B (mock); sửa safety stub → đo từ trace; **ablation replan trên harness A\* xác định** (ON 19/19 vs OFF 12/19; chưa chạy trên LLM agent) | ✅ Done | `run_eval.py`, `report.md` |
| Thái | Phase 5c: sửa bug **t01 done‑sớm**; `safe_behavior_rate` riêng; headline = 5 core category; dọn ablation gây hiểu lầm | ✅ Done | `observe_node.py`, `run_eval.py` |

**Tổng kết:** eval **trung thực**: agent Gemini thật **100% core (7 task lõi · n=8)**, replan ablation **trên harness A\* xác định (chưa chạy trên LLM agent)**, `safe_behavior_rate 100%`, `safety_events_handled=3` (0 va chạm là do sim chặn cứng); tách bạch mock baseline. Quyết định **thu hẹp** vào lõi đã chứng minh (xem JOURNAL).

---

## 2026‑06‑06 — Phase 6 + 7 (Showcase sản phẩm: replay + đa năng lực + audit) ✅

| Member | Task | Status | Output |
|--------|------|--------|--------|
| Mạnh | Phase 6: chế độ **Phát lại** (fixture run thật, không tốn quota) + hero scenario + panel 429/quota; StaticFiles phục vụ frontend | ✅ Done | `frontend/`, `replays/` |
| Đạt | Phase 6: deploy config (Dockerfile + `render.yaml`) + `DEPLOY_runbook.md`; `/health` | ✅ Done | deploy config |
| Mạnh | Phase 7: **đa năng lực** (chip + replay: giao/replan/an toàn/nói‑không) + nhãn **grounded** mỗi trace + **⤓ xuất audit log** | ✅ Done | `frontend/` |
| Thái | Phase 7: khối **Ứng dụng** + **lộ trình tới robot thật** (trung thực) + gợi ý vật/zone; `/replays` 404 nhẹ; WS reconnect 1 lần | ✅ Done | `frontend/` |

**Tổng kết:** `pytest -q` → **72 passed**; `ruff` → All checks passed. Showcase chứng minh agent **giải đủ kiểu việc + kiểm chứng được (grounded + audit log) + có đường ra robot thật** — đúng chủ đề #162.

---

## [YYYY‑MM‑DD] — Trước nộp (còn lại) ⏳

| Member | Task | Status |
|--------|------|--------|
| Đạt | Deploy Render → live URL (theo `DEPLOY_runbook.md`); xác nhận LangSmith có trace | ⏳ Next |
| Mạnh | Quay video 3' (theo `video_script.md`); thu ≥3 feedback (`eval/USER_FEEDBACK.md`) | ⏳ Next |
| Cả nhóm | Điền MSSV Mạnh; rà `SUBMISSION_CHECKLIST.md` rồi nộp | ⏳ Next |

---

<!-- Copy block cho mỗi ngày build. Cập nhật tên & số giờ thật. -->
