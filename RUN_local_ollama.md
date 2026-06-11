# Chạy agent bằng LLM local (Ollama) + metric đánh giá

Thay đổi này **tạm thời, chỉ trên máy này**: code mặc định vẫn là Gemini cloud,
còn `.env` đã đặt `LLM_PROVIDER=ollama` để chạy local. Đổi lại 1 dòng là revert.

## 1. Chuyển sang local (đã làm sẵn trong `.env`)

```env
LLM_PROVIDER=ollama          # gemini = cloud (mặc định) | ollama = local
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b      # PHẢI hỗ trợ tool-calling (qwen2.5 / llama3.1)
```

Cài và khởi động Ollama:

```bash
pip install langchain-ollama
ollama pull qwen2.5:7b
ollama serve                 # để chạy ở một cửa sổ riêng
```

Revert về cloud: đặt lại `LLM_PROVIDER=gemini` trong `.env` (không cần sửa code).

## 2. Metric đánh giá agent (Bảng A của `eval/run_eval_v2.py`)

Ngoài `success_rate` và `latency/bước` đã có, bổ sung 4 metric phù hợp cho
agent task-planner:

| Metric | Ý nghĩa |
|---|---|
| **SPL (path-efficiency)** | `success × đường_tối_ưu / max(tối_ưu, thực_tế)`. So quãng đường robot với lời giải A* tối ưu — đo hiệu quả chứ không chỉ đúng/sai. |
| **valid_action_rate** | Tỉ lệ bước gọi tool hợp lệ (đúng schema, không lỗi) trên tổng số bước. |
| **infeasible/abstention accuracy** | Tỉ lệ nhận diện đúng task bất khả thi (từ chối thay vì bịa kế hoạch). |
| **LLM calls + replans/task** | Chi phí: số lần gọi LLM (suy ra từ cấu trúc đồ thị) và số lần replan mỗi task. |

Honesty check: cảnh báo nếu agent tự khai `done` nhưng oracle xác nhận chưa đạt
(ảo tưởng hoàn thành). Success luôn chấm bằng oracle độc lập, không tin status agent.

## 3. Chạy eval

```bash
python eval/run_eval_v2.py            # Bảng B — solver A* tất định (không cần LLM)
python eval/run_eval_v2.py --seeds 3  # + Bảng A — agent thật (local Ollama), 3 seed/task
```

Kết quả ghi ở `eval/results/report_v2.md` và `eval/results/metrics_v2_agent.csv`.
Tiêu đề Bảng A ghi rõ backend (Ollama:qwen2.5:7b) — số local và cloud không trộn lẫn.
