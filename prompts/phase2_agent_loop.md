# Prompt Phase 2 cho Claude Code — LangGraph plan loop + Gemini (AI20K‑162)

> Dán nguyên khối dưới đây vào Claude Code (đang mở repo App‑022), **sau khi Phase 1 (9 tool) đã xong & test xanh**.
> Bối cảnh: Phase 0 (World+A*+render) ✅, Phase 1 (9 tool thao tác World + pytest) ✅. Giờ ráp **vòng agent** bằng LangGraph + **Gemini function‑calling**, stream trace qua WebSocket. Dừng cuối phase để review.

---

```
Đọc PLAN_agent_taskplanner.md (mục 5,6,7,11), STRATEGY_162.md (§9), src/agents/tools/ và src/services/world.py.
Làm PHASE 2: vòng agent LangGraph + Gemini function-calling + stream trace. DỪNG để review khi xong.

## BƯỚC 0 — Chốt LLM provider = Gemini (đồng bộ toàn repo)
- requirements.txt: thay `langchain-openai` -> `langchain-google-genai>=2.0.0`. Cài lại.
- src/config.py: thay khối OpenAI bằng:
    gemini_api_key: str = ""        # đọc từ GEMINI_API_KEY
    model_name: str = "gemini-flash-latest"
    llm_temperature: float = 0.2
  XOÁ các field không dùng: openai_api_key, database_url, chroma_persist_dir.
  Thêm: max_steps: int = 40, max_replans: int = 5.
- src/services/llm.py: khởi tạo `ChatGoogleGenerativeAI(model=settings.model_name,
  google_api_key=settings.gemini_api_key, temperature=settings.llm_temperature)`.
- .env.example đã sẵn GEMINI_API_KEY (không sửa).

## BƯỚC 1 — State (src/agents/state.py)
Thay AgentState boilerplate bằng schema thật (PLAN mục 6):
  goal_text:str, goal:dict|None, plan:list[str], history:list[dict], world_view:dict,
  status:str, replans:int, steps:int, answer:str, pending_question:str|None
Xoá file/test boilerplate cũ (example_node, test_graph cũ) — thay bằng node thật.

## BƯỚC 2 — Tools cho LLM (function-calling)
- Bọc 9 tool Phase 1 thành tool function-calling cho Gemini: tên + docstring mô tả + JSON params
  (LangChain `@tool` hoặc bind_tools). Tool THẬT thao tác `get_current_world()` và trả observation thật.
- Cấm hallucinate: node `act` PHẢI gọi tool và đọc observation thật, không để LLM bịa kết quả.

## BƯỚC 3 — Nodes (src/agents/nodes/*.py), mỗi node 1 file, hàm ngắn
- parse_goal: NL tiếng Việt -> goal {target, destination, constraints[]} (gọi Gemini, có schema).
- perceive: gọi tool perceive -> world_view.
- plan: Gemini sinh danh sách bước (dựa goal + world_view).
- act: thực thi 1 bước = chọn & gọi 1 tool (function-calling) -> ghi history {action,args,observation,ok}.
- observe: đọc kết quả; nếu đạt mục tiêu -> summarize; nếu còn bước -> act; (Phase 3 sẽ thêm replan/ask).
- summarize: sinh answer + trace gọn.
- (Phase 2 CHƯA cần replan/ask_human node — để Phase 3; nhưng đặt sẵn chỗ rẽ nhánh trong observe.)

## BƯỚC 4 — Graph (src/agents/graph.py)
- StateGraph: parse_goal -> perceive -> plan -> act -> observe -(loop)-> act / -> summarize -> END.
- CAP an toàn: dừng khi steps>max_steps -> summarize (status="failed", lý do rõ). Không treo.

## BƯỚC 5 — API (src/api/routes.py, src/main.py)
- POST /api/v1/run  body {goal_text} -> chạy agent -> trả {plan, history(trace), answer, status}.
- WS /ws: stream từng bước (status, action, observation, world_view) để frontend render realtime.
- Giữ GET /api/v1/world, POST /api/v1/scenario, GET /health.

## BƯỚC 6 — LangSmith (AI logs, deliverable #4)
- Bật tracing qua env (LANGCHAIN_TRACING_V2/PROJECT) — không hardcode key.

## BƯỚC 7 — Tests (pytest)
- test_graph: với 1 LLM **mock/fake** (không gọi mạng) → vòng parse->...->summarize kết thúc, history có bước.
- test_run_endpoint: POST /run trả 200 + có plan/trace (LLM mock).
- Giữ toàn bộ test Phase 0 + Phase 1 xanh. ruff sạch.

## RÀNG BUỘC
type hints đầy đủ; hàm ngắn; KHÔNG bare except; .env không commit; cap loop; tool đọc observation thật.

## KHI XONG
Liệt kê đã làm + test gì; dán `pytest -q` & `ruff check src tests`. DỪNG, không nhảy sang Phase 3.
```

---

## Ghi chú cho Thái (trước khi chạy)
- Cần **`GEMINI_API_KEY`** thật trong `.env` (Google AI Studio, free tier) để chạy demo; test thì dùng **LLM mock** nên không tốn quota.
- Sau khi Phase 2 xanh: bảo Cowork **review + cập nhật WORKLOG/JOURNAL** và ra `prompts/phase3_replan_safety.md`.
- `gemini-flash-latest` là model rẻ/nhanh hợp demo; nếu function‑calling cần mạnh hơn, đổi `MODEL_NAME` trong `.env` (không phải sửa code).
