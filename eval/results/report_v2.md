# Báo cáo eval v2 — di chuyển 1 vật thể

> Nguồn sự thật duy nhất cho số liệu v2. Công thức: `success_rate = task done / task feasible`, luôn kèm **n**. Success chấm bằng **oracle độc lập** (`check_object_moved`), không tin status agent.

> Hai lớp TÁCH BẠCH: **Bảng A = agent thật (LLM)**, **Bảng B = solver xác định (KHÔNG phải agent)**. Mock không bao giờ được gắn nhãn 'agent'.


## Bảng A — Agent thật (LLM, LangGraph)

- n = **11** lần chạy (9 task feasible × 1 seed; +2 run infeasible)


| Chỉ số | Kết quả (mean ± std) | Mục tiêu |
|---|---|---|
| success_rate (feasible) | **0% ± 0.0%** | ≥90% |
| SPL (path-efficiency) | **0.0 ± 0.0** | ≥0.80 |
| valid_action_rate | 0.8% ± 1.6% | ≥95% |
| infeasible/abstention accuracy | 100.0% (2/2) | 100% |
| LLM calls/task | 42 ± 0.0 | (báo thật) |
| replans/task | 0 | (báo thật) |
| latency/bước | 6.11s ± 2.01s | (báo thật) |

*SPL = success × optimal_path / max(optimal, actual). valid_action_rate = bước có tool-call hợp lệ / tổng bước. LLM calls suy ra từ cấu trúc đồ thị (parse+plan+replan+act).*


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

- Metric đánh giá agent: **success_rate, SPL (path-efficiency), valid_action_rate, infeasible/abstention accuracy, LLM calls + replans (cost)**. SPL & cost so với lời giải A* tối ưu — đo hiệu quả, không chỉ đúng/sai.

- Backend LLM ghi rõ ở tiêu đề Bảng A (Gemini cloud hay Ollama local). Số local & cloud KHÔNG trộn trong cùng một bảng.

