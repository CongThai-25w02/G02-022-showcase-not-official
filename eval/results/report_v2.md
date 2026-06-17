# Báo cáo eval v2 — di chuyển 1 vật thể

> Nguồn sự thật duy nhất cho số liệu v2. Công thức: `success_rate = task done / task feasible`, luôn kèm **n**. Success chấm bằng **oracle độc lập** (`check_object_moved`), không tin status agent.

> Hai lớp TÁCH BẠCH: **Bảng A = agent thật (LLM)**, **Bảng B = solver xác định (KHÔNG phải agent)**. Mock không bao giờ được gắn nhãn 'agent'.


## Bảng A — Agent thật (LLM, LangGraph)

- n = **33** lần chạy (9 task feasible × 3 seed; +6 run infeasible)


| Chỉ số | Kết quả (mean ± std) | Mục tiêu |
|---|---|---|
| success_rate (feasible) | **70.4% ± 33.1%** | ≥90% |
| pass^k — success ở CẢ k=3 seed (τ-bench) | **44.4%** | ≥80% |
| SPL (path-efficiency) | **0.395 ± 0.438** | ≥0.80 |
| path_overhead (đi thật/tối ưu, run thành công) | 4.86 ± 4.75 | ≤1.25 |
| completion_rate (không timeout/error) | 100.0% (33/33) | 100% |
| valid_action_rate | 98.6% ± 3.4% | ≥95% |
| grounded_action_rate (mutate có quan sát trước) | 40.1% ± 39.4% | ≥95% |
| infeasible/abstention accuracy | 100.0% (6/6) | 100% |
| hallucinated_done_rate (tự khai done, oracle bác) | 0.0% (0/33) | 0% |
| LLM calls/task | 30.2 ± 15.0 | (báo thật) |
| replans/task | 0 | (báo thật) |
| latency/bước | 4.56s ± 0.56s | (báo thật) |

*SPL = success × optimal_path / max(optimal, actual). valid_action_rate = bước có tool-call hợp lệ / tổng bước. pass^k = % task thành công ở cả k seed (đo độ ổn định, τ-bench). grounded_action_rate = % move/pick/drop có perceive/locate/check_path thành công trước đó trong episode. LLM calls suy ra từ cấu trúc đồ thị (parse+plan+replan+act). Định nghĩa & nguồn: SURVEY_metrics.md.*


## Bảng B — Solver xác định (A*, KHÔNG phải agent)

- n = **9** task feasible; success_rate = **100.0%**; infeasible_correct = **2/2**


| id | category | feasible | success | status | steps |
|---|---|---|---|---|---|
| m01_basic_a | basic | True | True | done | 4 |
| m02_basic_b | basic | True | True | done | 4 |
| m03_basic_c | basic | True | True | done | 4 |
| m04_obstacle_wall | obstacle | True | True | done | 4 |
| m05_obstacle_detour | obstacle | True | True | done | 4 |
| m06_obstacle_narrow | obstacle | True | True | done | 4 |
| m07_pickdrop_far | pick/drop | True | True | done | 4 |
| m08_pickdrop_cross | pick/drop | True | True | done | 4 |
| m09_language_case | language | True | True | done | 4 |
| m10_infeasible_missing | infeasible | False | False | object_not_found | 0 |
| m11_infeasible_enclosed | infeasible | False | False | unreachable_object | 1 |

> Bảng B chỉ chứng minh **môi trường giải được** và harness đúng — **không** phải năng lực của agent. Mọi tuyên bố về agent phải lấy từ Bảng A.


## Trung thực & Disclosure

- Bộ task: di chuyển 1 vật thể (basic/obstacle/pick-drop/language) + ca infeasible.

- Không có người động / replan / 'an toàn' trong scope v2 → không khoe các chỉ số đó.

- Latency báo nguyên trạng; đây là planner mức nhiệm vụ, không phải vòng điều khiển realtime.

- Metric đánh giá agent: **success_rate, pass^k (reliability), SPL + path_overhead (efficiency), completion_rate, valid_action_rate, grounded_action_rate, infeasible/abstention accuracy, hallucinated_done_rate (honesty), LLM calls + replans (cost)**. So với lời giải A* tối ưu — đo hiệu quả, không chỉ đúng/sai. Khảo sát & định nghĩa: `SURVEY_metrics.md`.

- Backend LLM ghi rõ ở tiêu đề Bảng A (Gemini cloud hay Ollama local). Số local & cloud KHÔNG trộn trong cùng một bảng.

