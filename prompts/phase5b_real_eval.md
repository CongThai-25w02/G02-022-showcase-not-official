# Prompt cho Claude Code — PHASE 5b (Eval TRUNG THỰC: agent thật + sửa metric)

> Dán vào Claude Code. Lý do: bảng eval hiện tại **đo bằng MockPlanner (A* xác định), KHÔNG phải agent Gemini** → 3 vấn đề trung thực phải sửa trước khi đưa lên pitch. Giữ mock làm baseline, nhưng tách bạch và đo agent thật.

## 3 vấn đề cần sửa (có dẫn chứng `eval/run_eval.py`)

1. **Số trong report là của MOCK, không phải agent.** `avg_latency_per_step = 0.001s`, mọi status là của `MockPlanner` (`fail_no_static_path`, `asked_human`…). `MockPlanner` không gọi LLM. ⇒ "success 100%" KHÔNG chứng minh agent Gemini chạy đúng.
2. **`safety_violations` là stub luôn = 0.** `_count_safety_violations()` (dòng ~448) lặp nhưng **không bao giờ tăng**; mock cũng không tăng. World vốn chặn robot đi vào ô có người ⇒ "0 vi phạm" là **tất yếu theo cấu trúc**, không phải phép đo. Giám khảo sẽ chỉ ra ngay.
3. **`avg_replan_count = 0` mâu thuẫn với ablation "replan +66%".** Trong mock, `replan_enabled` thực chất bật/tắt **A* né người** (`astar` vs `astar_static`) chứ không phải node replan ⇒ né người mà `replans` vẫn 0. Headline "replan" đang gán nhãn sai.

```
NHIỆM VỤ PHASE 5b:

A) ĐO AGENT GEMINI THẬT (bằng chứng chính):
   1. Chạy `--llm gemini` trên một SUBSET tiêu biểu (hợp quota free tier ~10 req/phút), vd 8 task:
      t01,t03,t05,t07,t09,t11,t12,t15 (phủ basic/obstacle/pick/language/replan×2/safety/infeasible).
      Giữ throttle sleep sẵn có; timeout/task hợp lý.
   2. Ghi kết quả agent thật ra `eval/results/metrics_gemini.csv` và một mục RIÊNG trong report.md:
      "## A. Agent thật (Gemini) — N task tiêu biểu" với success_rate, avg_latency_per_step (thực,
      sẽ >0.1s), avg_replans (thực, từ node replan), invalid_tool_calls, infeasible_correct.
   3. Mục mock đổi tiêu đề thành "## B. Mock reference solver (A* xác định — baseline kiểm tra
      World/kịch bản, KHÔNG phải agent)" và đủ 18 task cho coverage.
   4. Thêm 1 dòng disclosure đầu report: "Bảng A đo agent Gemini thật; Bảng B là solver xác định
      để kiểm môi trường — không phải agent."

B) SỬA METRIC SAFETY cho THẬT:
   - Bỏ stub. Đo thật từ history/sim: đếm số lần robot **định** đi vào ô có người (bị World chặn →
      phải wait/ask) và xác nhận **0 lần thực sự chiếm ô của người**. Báo cáo dạng:
      `safety_events_handled` (số lần gặp người được xử lý đúng bằng wait/ask) + `safety_violations`
      (đi xuyên thật — kỳ vọng 0, nhưng phải là phép đo từ trace, không hardcode).
   - Nếu World đảm bảo cứng thì ghi rõ caveat: "0 vi phạm do World chặn cứng; chỉ số có nghĩa là
      agent có **dừng/hỏi đúng** khi gặp người" → đo `safety_events_handled` làm chính.

C) ABLATION REPLAN THẬT (trên graph Gemini, không phải mock):
   - Dùng đường `_run_with_gemini(replan_enabled=False)` (đã có monkeypatch route replan→summarize)
      chạy subset replan/safety với Gemini ON vs OFF → bảng so sánh có **replan_count thực > 0** ở ON.
   - Trong report ghi rõ: ablation ở Bảng A là "node replan ON/OFF" (agent thật); ở Bảng B (mock)
      là "A* né người ON/OFF" — ĐỪNG gộp nhãn.

RÀNG BUỘC: không phá Phase 0–5; pytest+ruff xanh; không commit secret; nếu quota Gemini hết giữa
chừng → ghi rõ "đo được k/N task" (trung thực), không bịa phần còn lại.

DoD:
- report.md có MỤC A (agent Gemini thật, latency thực >0.1s, replan_count thực) tách bạch MỤC B (mock).
- safety là phép đo từ trace (không phải stub), có caveat đúng.
- ablation replan thật (Gemini) cho thấy ON > OFF với replan_count > 0.
- pytest+ruff xanh. Xong thì DỪNG, dán 2 bảng A/B để mình (Cowork) viết diễn giải + đưa vào pitch.
```

---

> **Vì sao đáng làm:** một con số **70–85% của agent Gemini thật** (kèm caveat) **đáng tin và ăn điểm hơn nhiều** so với "100%" của solver xác định mà giám khảo bóc ra là không phải agent. Đúng tinh thần "Thật vs Mô phỏng" của đội — và chính điểm khác biệt này (đo thật + thừa nhận giới hạn) là thứ ít đội làm.
