# Survey metric khả thi cho AI20K‑162 (RoboPlanner)

> Ngày: 2026‑06‑10 · Đối chiếu harness hiện tại (`eval/run_eval_v2.py`) với chuẩn eval agent/embodied‑AI 2024–2026 (τ‑bench, ALFRED/SPL, LoTa‑Bench, ReliabilityBench).
> Phạm vi: **Bảng A/B (2D)** + **Bảng C (Gazebo)**. KPI sản phẩm/pilot: ngoài phạm vi file này.

## TL;DR

Bộ metric hiện tại đã **đúng chuẩn và khá đủ** (success oracle, SPL, valid_action_rate, abstention, cost, latency, hallucinated_done — ngang tầm benchmark công bố). Khả quan nhất còn thiếu là nhóm **reliability** (pass^k — chuẩn τ‑bench) và **grounding** (% hành động có quan sát trước) — cả hai tính được **từ dữ liệu sẵn có, 0 LLM call thêm**, và đúng câu chuyện "agent kiểm chứng được" cho giám khảo. Đã implement 5 metric quick‑win vào `run_eval_v2.py` (mục 2).

| Metric | Đo gì | Trạng thái | Công sức |
|---|---|---|---|
| success_rate (oracle) | đúng/sai nhiệm vụ | ✅ đã có | — |
| SPL | success × hiệu quả đường đi | ✅ đã có | — |
| valid_action_rate (≈ executability) | tool‑call hợp lệ | ✅ đã có | — |
| infeasible/abstention accuracy | biết "nói không" | ✅ đã có | — |
| LLM calls, replans, latency/bước | chi phí | ✅ đã có | — |
| **pass^k** | độ tin cậy qua k seed | 🆕 **đã thêm** | 0 (tính từ CSV) |
| **completion_rate** | % run không timeout/error | 🆕 **đã thêm** | 0 |
| **hallucinated_done_rate** | tự khai done nhưng oracle bác | 🆕 **đã thêm** (trước chỉ là warning) | 0 |
| **path_overhead** | quãng đi thật / tối ưu (run thành công) | 🆕 **đã thêm** | 0 |
| **grounded_action_rate** | % hành động mutate có perceive/locate/check_path trước | 🆕 **đã thêm** | 0 |
| token cost/task | chi phí thật ($, token) | ⏳ nên thêm | ~1h |
| latency tách plan vs execute | trả lời Q&A latency | ⏳ nên thêm (P1.3 sprint) | ~1–2h |
| paraphrase robustness | bền với cách diễn đạt tiếng Việt | ⏳ nên thêm nếu dư | ~2h |
| Bảng C: parity rate, sim‑gap, wall‑clock | sim→real | ⏳ theo PLAN_may_B §11 | đã lên kế hoạch |
| GCR/goal‑condition, safety, LLM‑judge | — | ❌ không đáng làm v2 | — |

---

## 1. Đã có — đối chiếu chuẩn

- `success_rate` chấm bằng oracle độc lập = đúng cách ALFRED/LoTa‑Bench (so trạng thái cuối với goal condition, không tin agent). Giữ nguyên.
- `SPL` = chuẩn embodied‑AI (Anderson et al.), harness đã tính đúng công thức `S·ℓ*/max(ℓ*,ℓ)`.
- `valid_action_rate` tương đương **executability** trong văn liệu planner.
- `infeasible_correct` + `hallucinated_done`: ít benchmark nào có — đây là **điểm khác biệt**, nên nâng từ ghi chú lên metric chính thức (đã làm).

## 2. Quick‑win — ĐÃ IMPLEMENT vào `run_eval_v2.py`

1. **pass^k** (τ‑bench): task được tính đạt khi thành công ở **cả k seed**. `pass^1` = success_rate; khoảng cách `pass^1 − pass^k` chính là độ "phập phù" của agent. Chạy `--seeds 3` là có. Đúng luận điểm trust: *robot kho cần đúng MỌI lần, không phải trung bình*.
2. **completion_rate**: % run kết thúc có kiểm soát (không `timeout`/`error:*`). Bảng A hiện tại 0/11 (toàn timeout 120s) — metric này lộ vấn đề vận hành mà success_rate che mất, và cho biết khi nào số khác đáng tin.
3. **hallucinated_done_rate**: % run agent tự khai `done` nhưng oracle bác. Headline "honesty" — 0% là con số đáng khoe; >0% là bằng chứng vì sao cần oracle.
4. **path_overhead** = `agent_distance / optimal_distance` trên run thành công (mean ± std). Tách phần "hiệu quả" ra khỏi SPL (SPL trộn success lẫn efficiency nên khó diễn giải khi success thấp).
5. **grounded_action_rate**: % hành động mutate (`move_to/pick/drop`) được thực hiện **sau khi** đã có ít nhất một quan sát (`perceive/locate_object/check_path`) trong episode. Đây chính là số đo cho KPI pilot "% hành động grounded" (P2.2 sprint) — giờ có công thức và số thật.

Tất cả tính từ `history`/CSV sẵn có — **không tốn thêm LLM call, không đổi schema task**.

## 3. Nên thêm trước demo day (effort trung bình)

- **Token + cost/task**: lấy `response.usage_metadata` (LangChain) cộng dồn vào state; báo `tokens/task` và quy ra $ theo giá flash‑lite. Trả lời thẳng câu "chạy tốn bao nhiêu?" của giám khảo đầu tư.
- **Latency tách lớp** (P1.3 đã ghi trong sprint): đo riêng *vòng plan (có LLM, ~giây)* vs *vòng thực thi sim (không LLM, ms)* — đập đúng Q&A "4.4s/bước thì ai dùng?". Cách rẻ: `time.perf_counter()` quanh từng node, cộng theo loại node.
- **Paraphrase robustness**: 3–5 cách diễn đạt tiếng Việt cho cùng 1 task (m09 đã có 1 ca "language") → báo success theo nhóm paraphrase. Chỉ làm nếu P0 xong sớm.

## 4. Bảng C — Gazebo (khớp `PLAN_may_B_gazebo.md` §11)

| Metric | Định nghĩa | Ghi chú |
|---|---|---|
| success (oracle ground‑truth) | như Bảng A, ≥3 task m\* | n nhỏ, ghi rõ |
| **tool‑sequence parity** | % trùng chuỗi tool 2D vs Gazebo cùng goal (exact hoặc Levenshtein) | bằng chứng "1 agent – 2 backend" mạnh nhất |
| **sim‑gap** | SR_2D − SR_Gazebo trên cùng task | con số sim→real trung thực |
| wall‑clock/task + startup time | thời gian chạy + boot <5' | độ bền demo |
| demo reliability | 5 lần chạy liên tiếp không fail (x/5) | §11.2 đã định nghĩa |
| detector mode | ground‑truth hay ARMBench, per‑task | disclosure, không phải số khoe |

## 5. KHÔNG đáng làm ở v2

- **GCR / goal‑condition success**: task v2 chỉ có 1 goal condition (vật ở đích) → GCR ≡ success. Chỉ có nghĩa khi quay lại multi‑goal (t06).
- **Safety/collision metrics**: sim chặn cứng → số luôn 0, không phải phép đo (đã ghi đúng trong PRD §13). Đừng thêm lại.
- **LLM‑as‑judge chất lượng plan**: tốn quota, chủ quan, mâu thuẫn triết lý "oracle độc lập".
- **pass@k** (ít nhất 1/k thành công): dễ nhầm với pass^k và kể câu chuyện ngược (che giấu sự phập phù) — tránh.

## Nguồn

- τ‑bench / pass^k: [arxiv.org/abs/2406.12045 (OpenReview)](https://openreview.net/forum?id=roNSXZpUDN)
- Survey eval LLM agents: [arxiv.org/abs/2503.16416](https://arxiv.org/html/2503.16416v2)
- LoTa‑Bench (task planner embodied): [arxiv.org/abs/2402.08178](https://arxiv.org/abs/2402.08178)
- ReliabilityBench (k‑trial, perturbation): [arxiv.org/html/2601.06112v1](https://arxiv.org/html/2601.06112v1)
- EMMOE (SR/SPL/subgoal cho mobile manipulation): [arxiv.org/abs/2503.08604](https://arxiv.org/pdf/2503.08604)
