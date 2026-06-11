# Prompt cho Claude Code — PHASE 5 (Eval + Deploy + Deliverables)

> Dán nguyên khối dưới đây vào Claude Code (mở trong repo `C2-App-022`).
> Phase 0–4 đã xong (65 test xanh, demo trình duyệt chạy). Phase 5 = **bằng chứng số (eval) + live URL + AI logs** — phần ăn điểm Product/System/DevOps và đóng nốt 10 deliverable.

---

```
Bối cảnh: repo C2-App-022, agent AI20K-162 đã xong Phase 0–4 (World sim + 9 tool + LangGraph
parse→perceive→plan→act→observe→replan→summarize + Gemini + UI animate/trace, 65 pytest xanh).
ĐỌC KỸ eval/scenarios/SPEC.md (thiết kế eval: taxonomy 18 task + metrics + ablation) và
ARCHITECTURE.md §"DevOps". CHỈ LÀM PHASE 5.

A) EVAL HARNESS (theo SPEC.md):
   1. Tạo đủ 18 scenario JSON `eval/scenarios/tNN_<slug>.json` theo taxonomy SPEC §2 và schema
      SPEC §1 (đã có warehouse_basic/blocked/dynamic — đổi tên/bổ sung cho đủ 18, gồm khối "task"
      với success/feasible/dynamic). Phủ: basic×2, obstacle×2, pick/drop×2, language×2, replan×3,
      safety×3, infeasible×2, robustness×2.
   2. `eval/run_eval.py`: nạp mọi `tNN_*.json` → chạy agent → chấm `success` bằng World thật →
      đếm metrics SPEC §3 (success_rate, safety_violations[=0 cứng], avg_steps, replan_count,
      invalid_tool_calls, infeasible_correct, latency_per_step) → ghi `eval/results/metrics.csv`
      + cập nhật bảng số trong `eval/results/report.md`.
   3. Cờ `--ablation`: chạy cùng 18 task với replan ON và OFF → sinh bảng so sánh theo category
      (SPEC §4) vào report + `metrics_ablation.csv`.
   4. **LLM cost:** hỗ trợ `--llm mock|gemini`. `mock` = planner xác định (đọc World, đi A* tới
      đích, pick/drop) để chạy eval + CI KHÔNG tốn quota. `gemini` = thật, có sleep/throttle hợp
      free tier (~10 req/phút). CI dùng mock.
   5. `tests/test_eval/`: smoke test 2–3 scenario tiêu biểu (mock LLM) chạy trong CI.

B) DEPLOY (live URL — deliverable #5):
   1. Đảm bảo app phục vụ CẢ backend + frontend tĩnh trong 1 service (FastAPI StaticFiles).
   2. Dockerfile (đã có) build chạy được; `HEALTHCHECK` gọi /health; docker-compose chạy local OK.
   3. Thêm `render.yaml` (hoặc Railway config) để deploy 1 lệnh; ghi `DEPLOY.md` ngắn (biến môi
      trường GEMINI_API_KEY + LANGCHAIN_* set ở dashboard, KHÔNG commit). Nếu không tự deploy được
      (cần tài khoản), để config sẵn + hướng dẫn để đội bấm deploy.

C) AI LOGS (LangSmith — deliverable #4):
   1. Bật tracing qua env (`LANGCHAIN_TRACING_V2=true`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT`)
      trong `.env.example` + đọc ở config; mỗi lần chạy agent log prompt + tool calls.
   2. Kiểm tra hook `.ai-log/` của BTC vẫn ghi khi `git push` (không phá).

D) DỌN & POLISH:
   1. Xoá boilerplate thừa nếu còn (`src/agents/nodes/example_node.py`, `tools/example_tool.py`).
   2. Cập nhật README: trạng thái Phase 5, badge số test thật, link live URL + eval report.
   3. `pytest -q` + `ruff check src tests eval` xanh.

RÀNG BUỘC:
- KHÔNG phá API/agent/UI Phase 0–4. Type hints + pytest + ruff. safety_violations PHẢI = 0 trên
  toàn bộ eval (nếu > 0 → bug an toàn, sửa trước khi báo xong).
- Không commit secret; `.env` trong `.gitignore`.

DoD PHASE 5 (tự kiểm):
- `python eval/run_eval.py --llm mock` → in metrics + ghi report.md/metrics.csv; success_rate nhóm
  feasible > 80%, safety_violations = 0.
- `python eval/run_eval.py --ablation --llm mock` → bảng on/off cho thấy replan nâng success ở
  nhóm replan/safety.
- `docker compose up` chạy; mở web thấy demo; /health OK.
- LangSmith nhận trace khi chạy 1 mục tiêu thật.
- `pytest -q` + `ruff` xanh.

Làm xong Phase 5: liệt kê file tạo/sửa + dán bảng metrics + link live URL (nếu deploy) + kết quả
test, rồi DỪNG. Đây là phase cuối phần code — sau đó mình (Cowork) ráp pitch/video + audit deliverable.
```

---

**Cowork làm song song khi Claude Code chạy Phase 5:** (1) diễn giải kết quả eval vào `report.md` + biểu đồ cột on/off; (2) **pitch deck 10 slide** + script video 3 phút; (3) **deploy runbook** double‑check; (4) audit **10 deliverable** trước hạn nộp.
