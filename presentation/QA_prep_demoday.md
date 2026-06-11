# Q&A Demo‑Day — Đối đáp câu hỏi khó (trung thực)

> Mục tiêu: không bị "bắt bài". Mỗi câu trả lời **thẳng thắn**, ngắn, kèm **bằng chứng để chỉ vào**. Trung thực là vũ khí — đừng phòng thủ, đừng overclaim.

## A. Câu hỏi kỹ thuật (giám khảo)

**1. "Đây là agent thật hay chỉ bọc Gemini + A\*?"**
→ Agent thật: **Gemini (function‑calling) tự chọn tool nào, theo thứ tự nào, và tự replan khi bị chặn** — không phải kịch bản cứng. A* chỉ là *một tool* (tìm đường); quyết định *khi nào đi/pick/drop/dừng/hỏi* là của LLM. **Bằng chứng:** ablation node replan kiểm chứng trên **harness A* xác định** (ON 19/19 vs OFF 12/19, *chưa chạy trên LLM agent*); riêng trên Gemini, **avg_replan_count 0→0.5** xác nhận node replan thật sự chạy (`eval/results/report.md`) + trace từng bước.

**2. "Sao là mô phỏng, không phải robot thật?"**
→ Ràng buộc 2 tuần + chỉ laptop, **không phần cứng**. Sim chứng minh đúng lớp khó về phần mềm: **ngôn ngữ → kế hoạch → kiểm chứng**. Bản sản xuất nối `move/pick` vào **ROS + perception camera**. Chúng tôi ghi rõ "thế giới mô phỏng · agent thật" — không giả vờ là robot.

**3. "Latency 4.3s/bước có dùng được không?"**
→ Đây là `gemini-flash-lite` free‑tier + mạng. Là **planner mức nhiệm vụ**, không phải vòng điều khiển realtime. Production: streaming + model nhanh hơn + cache. Số này chúng tôi **báo thật** trong eval, không giấu.

**4. "100% có quá đẹp không?"**
→ 100% trên **5 nhóm lõi** (7 task lõi), đo trên **agent Gemini thật** (không phải mock), **mẫu nhỏ n=8** do giới hạn quota — chúng tôi ghi rõ. An toàn không tính vào headline mà đo riêng bằng `safe_behavior_rate`. Bảng A (agent) tách bạch Bảng B (mock). Đó là lý do số đáng tin.

**5. "Làm sao tin agent không bịa (hallucinate)?"**
→ Tool **đọc trạng thái thật từ World** rồi mới quyết — LLM không tự "tưởng tượng" kết quả. Mỗi bước có nhãn **grounded** + nút **⤓ xuất audit log**. Eval: `invalid_tool_calls = 0%`.

**6. "Nếu gõ lệnh lạ / vật không có thì sao?"**
→ Agent **biết "nói không"** (báo bất khả thi) thay vì bịa — `infeasible_correct 100%`. UI gợi ý vật/zone hiện có để người dùng ra lệnh đúng.

**7. "An toàn khi robot gần người?"**
→ Thẳng: **vision/sim KHÔNG thay lớp an toàn cứng**. Lớp dừng khẩn phải là **LiDAR + cảm biến chứng nhận SIL/PL (ISO 3691‑4)**. Agent là **lớp ngữ nghĩa bổ trợ** + **human‑in‑loop** (gặp người sát → dừng & hỏi). 0 va chạm là do **sim chặn cứng** (không phải phép đo an toàn); chỉ số có nghĩa là agent **chủ động dừng/hỏi** (`safety_events_handled`).

## B. Câu hỏi đầu tư / kinh doanh

**8. "Moat đâu? Ai cũng ghép Gemini được."**
→ Đúng — **moat không ở model**. Khác biệt là **kỷ luật grounding + trace audit + phương pháp đo**, và (về sau) **tích hợp + dữ liệu vận hành**. Thẳng thắn: giai đoạn này moat còn mỏng; lợi thế là **đi sớm đúng nỗi đau 'trust'** + tốc độ.

**9. "Thị trường? Khách hàng? Mô hình?"**
→ Trong khuôn khổ **cuộc thi BTC** đây là dự án #162 (robot kho). *Nếu* nói chuyện đầu tư: giá trị fundable là **"lớp thực thi agent có kiểm chứng"** cho doanh nghiệp (agent audit được, không hallucinate) — robot kho chỉ là 1 ví dụ. (Chi tiết: `Investor_OnePager_AuditableAgents.md`.) Số liệu: 55% DN coi hallucination là rào cản #1 triển khai agent (Futurum 2026).

**10. "Khác gì AMR/robot kho đã có (Symbotic, Locus…)?"**
→ Không thay stack an toàn/điều hướng của họ — **bổ sung lớp ra‑lệnh‑bằng‑ngôn‑ngữ + kế hoạch + audit**, nơi các stack thuần hardware còn yếu.

**11. "Đội sinh viên thì lợi thế gì?"**
→ Đã tự build agent **chạy thật, grounded, có eval + audit** trong 2 tuần, và **văn hoá trung thực** (công bố mock‑vs‑thật, thừa nhận giới hạn) — đúng DNA để bán "trustworthy agents".

## Nguyên tắc trả lời
- **Thừa nhận giới hạn trước, mạnh sau** ("đây là sim, nhưng phần khó về agent đã chứng minh thật…").
- Luôn **chỉ vào bằng chứng** (eval report / audit log / ablation), không nói suông.
- Không bao giờ overclaim "robot thật" / "thay được lớp an toàn" — chính sự thẳng thắn ăn điểm.
