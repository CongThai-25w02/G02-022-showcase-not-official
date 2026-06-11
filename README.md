# AI20K‑162 — Agent lập kế hoạch tác vụ điều khiển robot kho bằng ngôn ngữ tự nhiên

[![CI](https://github.com/AI20K-Build-Cohort-2/starter-code-template/actions/workflows/ci.yml/badge.svg)](https://github.com/AI20K-Build-Cohort-2/starter-code-template/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11-blue)
![tests](https://img.shields.io/badge/tests-passing-brightgreen)
![lint](https://img.shields.io/badge/lint-ruff-46a2f1)
![license](https://img.shields.io/badge/license-MIT-green)
<!-- Nếu fork sang repo của đội, đổi "AI20K-Build-Cohort-2/starter-code-template" trong badge CI ở trên. -->

> Tóm tắt 1 câu (v2 thu nhỏ): **Vận hành viên ra mục tiêu bằng tiếng Việt** → **agent (LLM) tự lập kế hoạch và di chuyển ĐÚNG 1 vật thể** trong **kho mô phỏng 2D xác định, kiểm chứng được** (chấm bằng oracle độc lập, không hallucinate) — minh bạch, có người trong vòng lặp.

> **Đề tài:** AI20K‑162 (Lập kế hoạch tác vụ) **gộp** AI20K‑161 (Điều khiển bằng ngôn ngữ tự nhiên).
> **Trạng thái:** **v2 "thu nhỏ"** theo phản hồi mentor — chốt lõi **di chuyển 1 vật thể**, ưu tiên **simulation đúng & kiểm chứng được**. Sim đã khóa bằng **bất biến trạng thái** ([`src/services/invariants.py`](src/services/invariants.py), tự kiểm sau mỗi mutation) + **oracle độc lập** ([`src/services/oracle.py`](src/services/oracle.py)); agent graph có cờ **`core_scope`**. Kế hoạch v2: [`PLAN_thu_nho_162.md`](PLAN_thu_nho_162.md).
> **Eval v2 (nguồn sự thật duy nhất: [`eval/results/report_v2.md`](eval/results/report_v2.md)):** hai lớp **TÁCH BẠCH** — **Bảng A = agent thật (Gemini)** đo **mean ± std + n** (chạy `python eval/run_eval_v2.py --seeds 3` khi có `GEMINI_API_KEY`; chưa có key thì để trống, **không bịa số**); **Bảng B = solver xác định A\*** (**KHÔNG phải agent**) chứng minh môi trường giải được: **9/9 task feasible**, **infeasible_correct 2/2**. Success luôn chấm bằng **oracle**, không tin status agent tự khai. *(Số v1 cũ: `eval/results/report.md`.)*
> **Ràng buộc:** laptop + điện thoại, ~2 tuần, **không phần cứng robot** → robot **mô phỏng 2D**, agent **thật**.

## Vấn đề (Problem)

Điều khiển robot kho hiện cần lập trình từng bước, cứng nhắc khi môi trường đổi:

- **Vận hành viên (không phải kỹ sư)** không thể "ra lệnh" cho robot bằng ngôn ngữ thường — phải qua kỹ sư lập trình.
- **Môi trường động** (người, xe nâng, vật cản xuất hiện) → kịch bản lập sẵn hỏng, phải lập trình lại tay.
- **Hộp đen:** không biết robot định làm gì, có an toàn không → khó tin, khó kiểm.

## Giải pháp (Solution)

Một **agent lập kế hoạch** (LLM + tool‑calling) đứng giữa ngôn ngữ và hành động:

- **Feature 1 — Ra lệnh tiếng Việt tự nhiên:** "Đưa pallet A từ khu A sang chuyền 3, tránh người" → agent hiểu & thực thi (161).
- **Feature 2 — Lập kế hoạch + tự điều chỉnh:** phân rã mục tiêu thành chuỗi hành động, thực thi từng bước, **replan** khi bị chặn (162).
- **Feature 3 — Minh bạch + human‑in‑loop:** hiện **kế hoạch + trace lý luận** (suy nghĩ → tool → kết quả); khi **gặp người sát / không chắc** → agent **dừng & hỏi** (không đoán liều). Đây là hành vi đúng, không phải "bộ điều khiển an toàn".

> **Phạm vi v2 (thu nhỏ — chốt vào lõi kiểm chứng được):**
> **TRỌNG TÂM** = ra lệnh tiếng Việt → agent **lập kế hoạch và di chuyển 1 vật thể** tới đích qua kho có **chướng ngại tĩnh** → **drop đúng ô** (được oracle xác nhận). Bộ task: `eval/scenarios/m*.json` (sinh bằng `python eval/gen_move_tasks.py`).
> **Bonus minh bạch:** biết báo **"không làm được"** khi bất khả thi (2 ca infeasible trong bộ eval) · trace từng bước · xuất audit log.
> **Roadmap (đã CẮT khỏi v2 — không khoe như đã hoàn thành):** replan khi gặp **người động**, human‑in‑loop/an toàn ngữ nghĩa, voice, đa vật thể/đa robot, **lớp an toàn cứng** (LiDAR/cảm biến), cầu nối sim→real (ROS/perception). Mã các phần này vẫn còn nhưng **ngoài phạm vi đo của v2** (bật lại bằng cờ `core_scope=False`).

> **Trung thực:** thế giới là **mô phỏng 2D** (không phải robot thật); **agent là thật** (LLM lập kế hoạch + vòng tool thật, đọc kết quả thật từ sim, không "tưởng tượng").

## Target User

- **Primary:** vận hành viên kho/nhà máy muốn điều khiển robot bằng ngôn ngữ, không qua lập trình.
- **Secondary:** kỹ sư tích hợp robot (prototype nhanh logic nhiệm vụ); đội an toàn/QA cần kế hoạch minh bạch, kiểm chứng được.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Agent | **LangGraph + LangChain** (plan‑and‑execute + ReAct) |
| LLM | **Google Gemini** (`gemini-flash-latest`, function‑calling) |
| Backend | **FastAPI + Python 3.11** |
| Sim world | `World` engine Python (grid 2D, A*) — "có thẩm quyền" ở backend |
| Frontend | Web canvas 2D (render sim + bảng kế hoạch/trace), responsive + dark |
| Realtime | WebSocket (stream trace + trạng thái world) |
| Testing | pytest (tools, world, graph, eval) |
| DevOps | Docker + GitHub Actions + LangSmith (AI logs) |

## Quick Start

```bash
# 1. Môi trường
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. API key (KHÔNG commit)
cp .env.example .env
# điền GEMINI_API_KEY=... (Google AI Studio) + AI_LOG_API_KEY của BTC

# 3. Chạy backend (agent + sim + API)
uvicorn src.main:app --reload --port 8000
# Swagger: http://localhost:8000/docs

# 4. Mở giao diện sim (frontend) → nhập mục tiêu tiếng Việt → xem agent lập kế hoạch & chạy
```

## Project Structure

```
├── src/
│   ├── agents/
│   │   ├── graph.py        # LangGraph: parse→perceive→plan→act→observe→replan→summarize
│   │   ├── state.py        # AgentState (goal, plan, history, world_view, status…)
│   │   ├── routing.py      # decide_observe_route + cờ core_scope — NEW v2
│   │   ├── nodes/          # mỗi node 1 file
│   │   └── tools/          # perceive/locate/check_path/move/pick/drop/wait/ask/done
│   ├── services/
│   │   ├── world.py        # World sim (grid, A*) + tự kiểm bất biến sau mỗi mutation
│   │   ├── invariants.py   # assert_invariants — bất biến trạng thái sim — NEW v2
│   │   ├── oracle.py       # check_object_moved — chấm điểm độc lập — NEW v2
│   │   └── llm.py          # Gemini function-calling
│   ├── api/routes.py       # POST /api/v1/run · WS /ws · GET /health
│   ├── models/schemas.py   # Pydantic: Goal, Action, WorldState, StepTrace
│   └── main.py
├── frontend/               # canvas 2D + ô nhập mục tiêu + bảng trace
├── tests/                  # pytest: tools, world, graph, eval
├── eval/                   # gen_move_tasks.py (m*.json) · run_eval_v2.py · results/report_v2.md
├── PLAN_thu_nho_162.md     # kế hoạch v2 (scope + sim đúng + eval trung thực) — NEW
└── PLAN_agent_taskplanner.md  # scoping + kiến trúc v1
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/run` | Nhận `{goal_text}` → chạy agent → trả kế hoạch + trace + kết quả |
| WS | `/api/v1/ws` | Stream từng bước (suy nghĩ → tool → observation) + trạng thái world |

## Deliverables Checklist

- [x] Source Code (`src/`) — World + 9 tool + LangGraph + Gemini + UI + eval; **v2: invariants + oracle + cờ `core_scope` + bộ task move‑one‑object** · bộ test mở rộng (sim/oracle/property/routing)
- [x] README.md
- [x] Architecture Diagram (`docs/architecture_diagram.md`)
- [x] AI Logs (LangSmith) — đã cấu hình tracing
- [ ] Live URL / Deploy (Render/Railway) — config sẵn (`DEPLOY.md`), cần bấm deploy
- [ ] Video Demo — kịch bản 3 phút sẵn trong `PLAN_agent_taskplanner.md`
- [x] Pitch Deck (`presentation/pitch_deck.pptx`) — 10 slide (story thu nhỏ + số eval thật)
- [x] Weekly Journal (`JOURNAL.md`)
- [x] Worklog (`WORKLOG.md`)
- [x] Evaluation Evidence — **v2: [`eval/results/report_v2.md`](eval/results/report_v2.md)** (chấm bằng oracle; Bảng B xác định **9/9 feasible**, infeasible **2/2**; Bảng A agent chờ chạy với `GEMINI_API_KEY`). Tham khảo v1: `eval/results/report.md`.

## Team

| Member | Role | Student ID |
|--------|------|-----------|
| Lưu Công Thái | Agent core (LangGraph) + Gemini · Product lead | 2A202600949 |
| Lê Hữu Đạt | Sim World + Tools + FastAPI/backend | 2A202600630 |
| Nguyễn Đình Tiến Mạnh | Frontend (canvas/trace) + Evaluation + Demo | _[điền MSSV]_ |

> _Phân vai có thể điều chỉnh theo thực tế._

## License

MIT
