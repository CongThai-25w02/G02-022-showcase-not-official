# Prompt Phase 3 cho Claude Code — Replan + An toàn (AI20K‑162)

> Dán nguyên khối dưới đây vào Claude Code, **sau khi Phase 2 đã xong & test xanh (46 pass)**.
> Bối cảnh: vòng agent đã chạy (parse→perceive→plan→act→observe→summarize); `move_to` đã trả `blocked_by` khi gặp người, `observe` đã đặt `status="blocked"`, graph đã chừa nhánh route. Giờ làm **replan + an toàn (ask_human/wait) + người động** và **vá vài điểm review**. Dừng cuối phase để review.

---

```
Đọc STRATEGY_162.md (§9), eval/scenarios/SPEC.md, src/agents/graph.py, observe_node.py, act_node.py,
src/services/world.py. Làm PHASE 3. DỪNG để review khi xong.

## A. Node REPLAN (src/agents/nodes/replan_node.py)
- Khi observe -> status="blocked" (move_to gặp người): tăng state["replans"] += 1.
- Nếu replans > settings.max_replans -> status="failed" (kèm lý do) -> summarize.
- Ngược lại: gọi LLM sinh kế hoạch mới DỰA TRÊN blocked_by + world_view hiện tại
  (vd: đi đường vòng, hoặc wait, hoặc ask_human nếu người chắn lối duy nhất) -> set plan mới, status="acting".

## B. Node SAFETY (an toàn — ưu tiên cao hơn replan)
- Trước/într khi act: nếu có NGƯỜI trong bán kính kề robot (manhattan <=1) trên hướng đi:
  agent phải chọn `wait` (chờ người đi) hoặc `ask_human` — TUYỆT ĐỐI không move vào ô người.
- Bất biến cứng cần test: số lần robot vào ô có người = 0 (safety_violations == 0) trong mọi kịch bản.
- ask_human -> status="asking" -> summarize (dừng chờ người); trả pending_question ra API/WS.

## C. Người ĐỘNG (để wait/replan có ý nghĩa)
- Thêm vào scenario JSON khối "task.dynamic": lịch người di chuyển/spawn theo tick, vd:
    "dynamic": [ {"tick": 2, "person":"person-1", "to":{"x":7,"y":6}} ]
- World.advance_tick(n): áp lịch dynamic -> cập nhật vị trí người theo tick hiện tại.
- Nhờ vậy: bị chặn -> wait -> người đi khỏi -> move_to thành công (đường cũ), hoặc replan đường khác.

## D. Wire graph (src/agents/graph.py)
- _route_observe: status=="blocked" -> "replan" (KHÔNG còn fall-through summarize);
  status=="asking"|"done" -> "summarize"; steps>=max_steps -> summarize với status="failed".
- Thêm node "replan"; edge replan -> act (hoặc -> summarize nếu failed). Giữ cap chống treo.
- Cho summarize đọc status "failed"/"asking" để viết answer trung thực (không báo done giả).

## E. Vá điểm review Phase 2 (làm gọn)
1. act_node: chỉ thực thi **1 tool-call đầu tiên**/bước (1 action = 1 step) để trace + đếm step chuẩn.
2. check_path: trả luôn `blocker` (entity người trên đường) thay vì None, để ask_human nói rõ.
3. graph: wire cap_exceeded -> set status="failed" (đừng để summarize tưởng done).
4. XOÁ file thừa: src/agents/nodes/example_node.py, src/agents/tools/example_tool.py (không còn import).
5. Đồng bộ model: README/.env dùng `gemini-2.0-flash` cho khớp config (hoặc ngược lại) — chọn 1.

## F. Tests (tests/test_agents/, tests/test_world/) — LLM mock, không gọi mạng
- replan: kịch bản người chắn -> agent đổi kế hoạch -> cuối cùng reached (giả LLM trả tool calls theo kịch bản).
- safety: người sát robot -> agent KHÔNG vào ô người -> safety_violations == 0.
- dynamic: advance_tick di chuyển người đúng lịch; wait -> người rời -> move_to qua được.
- cap: vượt max_replans -> status="failed", không treo.
- Giữ toàn bộ test Phase 0–2 xanh; ruff sạch.

## RÀNG BUỘC
type hints; hàm ngắn; KHÔNG bare except; tool đọc observation thật; cap steps & replans; 0 đi xuyên người.

## KHI XONG
Liệt kê đã làm + test gì; dán `pytest -q` & `ruff`. DỪNG để review (Cowork sẽ cập nhật docs + ra prompt Phase 4 UI).
```

---

## Ghi chú cho Thái
- Sau Phase 3, **demo lõi đã đủ kể chuyện**: ra lệnh tiếng Việt → kế hoạch → người chắn → **replan/dừng‑hỏi** → hoàn thành (0 đi xuyên người). Đây là phần ăn điểm Product + System mạnh nhất.
- Nhóm kịch bản `replan` + `safety` trong `eval/scenarios/SPEC.md` nên tạo **ngay trong phase này** để test thật (không đợi Phase 5).
- Xong thì báo tôi: tôi cập nhật WORKLOG/JOURNAL + ra `prompts/phase4_ui.md` (UI/UX + bảng trace + badge DỪNG/HỎI).
