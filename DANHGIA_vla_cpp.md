# Đánh giá: có nên dùng `VinRobotics/vla.cpp` cho dự án AI20K-162?

> Ngày: 2026-06-10 · Repo: https://github.com/VinRobotics/vla.cpp (Apache-2.0, ~5 commit, 10 sao, mới)
> Liên kết: `KE_HOACH_FINAL_SPRINT.md`, `PLAN_may_B_gazebo.md`

## TL;DR
**Dùng được về pháp lý + chạy được trên Máy B, NHƯNG nó ở TẦNG KHÁC với dự án — KHÔNG tích hợp vào lõi trước deadline.** Giá trị tốt nhất = **một slide/đoạn "sim→real" trong pitch** (rủi ro ~0, đúng thông điệp, hợp gu giám khảo đầu tư). Tích hợp thật sẽ tốn tuần→tháng và phá vỡ luận điểm "agent kiểm chứng được".

## vla.cpp là gì
Runtime C++ (trên `llama.cpp`) chạy các **policy VLA end-to-end** (SmolVLA, π0, BitVLA, Evo-1, GR00T N1.5/1.6/1.7) đóng gói thành 1 file GGUF, không cần Python/PyTorch lúc inference. Kiến trúc `vla-server` (nạp model) ↔ client qua ZeroMQ/protobuf. Chạy CPU hoặc CUDA, tới được Jetson Orin Nano 8GB. Benchmark trên **LIBERO** và **SimplerEnv** (đều là gắp-đặt trên bàn — Panda/WidowX), SR 80–100%, VRAM 1.3–6 GB.

## Vì sao KHÔNG khớp với dự án
| | Dự án của bạn | vla.cpp |
|---|---|---|
| Tầng | **Planner nhiệm vụ** (LLM/LangGraph) ra lệnh symbolic `move_to/pick/drop` | **Policy điều khiển** end-to-end, xuất action liên tục (n_act 4–50) |
| Triết lý | **Kiểm chứng được**: grounded + trace + "biết nói không" | Mạng học **hộp đen**, không trace/không từ chối |
| Thực thi | Nav2 + MoveIt (cổ điển, ms, không LLM) | Chính nó *là* vòng điều khiển học được |
| Embodiment/task | Xe nâng/AMR trong kho (Gazebo + AWS world) | Cánh tay Panda/WidowX gắp đồ trên bàn |

→ vla.cpp nằm **dưới** agent của bạn (vòng thực thi). Thay nó vào lõi = vứt bỏ chính điểm mạnh nhất (System Design ~9 + góc đầu tư). Embodiment lại khác hẳn → muốn chạy trên xe nâng phải fine-tune + convert GGUF cho robot đó: ngoài tầm deadline.

## Làm được gì (3 mức)
1. **Điểm kể chuyện sim→real trong pitch — NÊN LÀM (phút).** Định vị: "Lớp plan+audit của chúng tôi cắm *lên trên* một policy học được. Đã có runtime VLA của người Việt (VinRobotics) làm nền thực thi." Củng cố Q&A sim-to-real (P2.5) + moat. Bonus: 1 contributor (An Thai Le) là người Việt → hợp câu chuyện hệ sinh thái VN.
2. **Benchmark LIBERO độc lập làm "đồ chơi trưng bày" — CHỈ KHI dư thời gian + Máy B có GPU NVIDIA.** ~0.5–1 ngày (build + tải GGUF từ HF `vrfai` + setup LIBERO qua `uv`). Nhưng nó *cạnh tranh* với Bảng C Gazebo đã lên kế hoạch — Bảng C đúng thông điệp hơn. Khuyến nghị: bỏ qua trừ khi P0 xong sớm.
3. **Tích hợp làm backend thực thi thật (VLA chạy `pick`/`drop`) — KHÔNG.** Sai embodiment, cần GPU (Máy B chưa chắc có), phải nối ZeroMQ/protobuf vào `GazeboBackend`, và mâu thuẫn câu chuyện audit. Tuần→tháng, không phải ngày.

## Đủ thời gian không?
**Không, cho việc tích hợp** — và cũng không nên. Sprint (>1 tuần) đã kín D1–D7 toàn việc ăn điểm trực tiếp (Bảng A, live URL, video, feedback, LangSmith) + Máy B giai đoạn 2. vla.cpp nằm **ngoài đường găng**.
- Tích hợp lõi: ✗ không khả thi trước hạn.
- Benchmark standalone: ~1 ngày, khả thi nhưng tranh chỗ việc giá trị hơn → chỉ nếu dư.
- Điểm pitch sim→real: ✓ vài phút, rủi ro ~0 → **làm cái này**.

## Khuyến nghị
Giữ nguyên kế hoạch sprint. Thêm **1 dòng vào slide sim→real + 1 câu Q&A** nhắc vla.cpp như tầng thực thi tương lai. Không viết code tích hợp lúc này.
