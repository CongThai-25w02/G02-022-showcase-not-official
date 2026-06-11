# PRD — AI20K‑162 "RoboPlanner"
### Agent lập kế hoạch tác vụ kho bằng ngôn ngữ tự nhiên (mô phỏng 2D)

| | |
|---|---|
| **Phiên bản** | 1.0 |
| **Ngày** | 2026‑06‑06 |
| **Trạng thái** | Phase 7 (v1) → **v2 "thu nhỏ"**: chốt lõi *di chuyển 1 vật thể*, ưu tiên sim đúng + oracle |
| **Chủ đề** | AI20K‑162 (Lập kế hoạch tác vụ) **gộp** AI20K‑161 (Điều khiển bằng ngôn ngữ tự nhiên) |
| **Nhóm** | App‑022 — Lưu Công Thái · Lê Hữu Đạt · Nguyễn Đình Tiến Mạnh |
| **Nguồn sự thật về số liệu** | **v2: [`eval/results/report_v2.md`](eval/results/report_v2.md)** · v1: [`eval/results/report.md`](eval/results/report.md) |
| **Tài liệu liên quan** | [`PLAN_thu_nho_162.md`](PLAN_thu_nho_162.md) · [`SPEC.md`](SPEC.md) · [`ARCHITECTURE.md`](ARCHITECTURE.md) · [`README.md`](README.md) |

---

> ⚠️ **Cập nhật v2 (thu nhỏ — theo phản hồi mentor).** Phạm vi đo của v2 là **di chuyển 1 vật thể** trong sim 2D **xác định, kiểm chứng được** (bất biến trạng thái + oracle độc lập; xem [`PLAN_thu_nho_162.md`](PLAN_thu_nho_162.md)). Các phần **replan khi người động, an toàn/human‑in‑loop, voice, đa robot** chuyển sang **Roadmap** — vẫn còn trong mã nhưng **không tính vào số liệu v2**. Nguồn số liệu v2 duy nhất: [`eval/results/report_v2.md`](eval/results/report_v2.md). Các mục dưới đây giữ nguyên thiết kế v1 đầy đủ làm **tham chiếu**.

## 1. Tóm tắt điều hành

RoboPlanner là một **agent (LLM) lập kế hoạch tác vụ**: vận hành viên ra **mục tiêu bằng tiếng Việt**, agent **tự phân rã thành chuỗi hành động**, thực thi từng bước trong một **kho mô phỏng 2D** thông qua các tool, **quan sát kết quả thật** từ sim và **tự lập lại kế hoạch (replan)** khi gặp người/vật cản. Toàn bộ suy luận được hiển thị **minh bạch** (kế hoạch + trace từng bước), và agent **dừng/hỏi người** khi không chắc, **biết báo "không làm được"** khi bất khả thi.

Khác biệt cốt lõi so với "một lời gọi LLM": đây là **vòng lặp agent thật** (plan → act → observe → replan) với **tool‑calling đọc trạng thái thật** — không để mô hình "tưởng tượng" kết quả. Thế giới là **mô phỏng**, nhưng **agent là thật**.

> **Trung thực có chủ đích:** thế giới 2D là môi trường chứng minh phương pháp trong ràng buộc ~2 tuần, chỉ laptop, **không phần cứng robot**. Phần khó về phần mềm — *ngôn ngữ → kế hoạch → kiểm chứng* — được làm thật và đo thật.

---

## 2. Bối cảnh & Vấn đề

Điều khiển robot kho hiện nay phải **lập trình từng bước**, cứng nhắc khi môi trường thay đổi. Ba nỗi đau cụ thể:

1. **Rào cản ngôn ngữ.** Vận hành viên (không phải kỹ sư) không thể "ra lệnh" cho robot bằng lời nói thường — mọi thay đổi phải qua kỹ sư.
2. **Môi trường động.** Người, xe nâng, vật cản xuất hiện bất ngờ làm kịch bản lập sẵn vỡ, phải lập trình lại bằng tay.
3. **Hộp đen, khó tin.** Không biết robot định làm gì, có an toàn không → đội an toàn/QA không dám đưa vào quy trình thật.

---

## 3. Mục tiêu & Phi mục tiêu

**Mục tiêu (Goals)**

- Cho phép ra lệnh **tiếng Việt tự nhiên** và để agent **tự lập kế hoạch nhiều bước** thực thi đúng.
- Agent **tự replan** khi bị chặn (người/vật cản) thay vì thất bại.
- **Minh bạch hoàn toàn**: hiển thị kế hoạch + trace *suy nghĩ → tool → kết quả thật*; cho **xuất audit log**.
- **An toàn có người trong vòng lặp**: gặp người sát / tình huống bất định → **dừng & hỏi**.
- **Không hallucinate**: mọi observation đọc từ trạng thái sim thật; biết **nói "không"** khi bất khả thi.
- Có **bằng chứng đo lường** (eval harness) tách bạch "agent thật" với baseline.

**Phi mục tiêu (Non‑goals) ở v1**

- Không điều khiển **robot phần cứng thật** (không ROS/cảm biến/động cơ).
- Không thay thế **lớp an toàn cứng** (LiDAR + cảm biến chứng nhận SIL/PL, ISO 3691‑4) — agent chỉ là **lớp ngữ nghĩa bổ trợ**.
- Không điều phối **đa robot**, không bản đồ lớn nhiều nhiễu, không tối ưu đường đi cấp công nghiệp.
- Không phải sản phẩm gọi vốn — đây là **proof‑of‑method** cho chủ đề thi #162.

---

## 4. Đối tượng người dùng & User stories

**Primary:** vận hành viên kho/nhà máy muốn điều khiển robot bằng ngôn ngữ, không qua lập trình.
**Secondary:** kỹ sư tích hợp robot (prototype nhanh logic nhiệm vụ); đội an toàn/QA cần kế hoạch kiểm chứng được.

User stories tiêu biểu:

- *Là vận hành viên,* tôi gõ "Đưa pallet A tới chuyền 3, tránh người" và robot tự làm, để tôi không phải lập trình.
- *Là vận hành viên,* khi có người chắn lối, tôi muốn robot **tự đổi đường** (hoặc dừng hỏi) thay vì kẹt/đâm.
- *Là QA,* tôi muốn **xem lại từng bước** robot đã nghĩ gì và đọc được gì, để audit độ an toàn.
- *Là vận hành viên,* khi tôi yêu cầu một vật **không tồn tại**, tôi muốn agent **báo không làm được** thay vì bịa.

---

## 5. Phạm vi

**Trong phạm vi (In scope)**

- Ra lệnh tiếng Việt → lập kế hoạch giao‑nhận qua kho có vật cản → **replan khi người chắn lối**.
- 3 kịch bản kho (cơ bản / có người chặn / người di chuyển động) + 19 task eval.
- Showcase web: render sim 2D, kế hoạch, trace, **phát lại (replay)**, **xuất audit log**, nhập **giọng nói** tiếng Việt.
- Bonus minh bạch: **dừng/hỏi** khi không chắc; **nói "không"** khi bất khả thi.

**Ngoài phạm vi (Out of scope)** — xem Phi mục tiêu (mục 3): robot thật, lớp an toàn cứng, đa robot, bản đồ lớn, RAG.

---

## 6. Tính năng & Yêu cầu

### F1 — Ra lệnh tiếng Việt tự nhiên
Người dùng nhập mục tiêu bằng tiếng Việt (gõ hoặc **giọng nói** vi‑VN). Agent phân rã thành {mục tiêu, đích đến, ràng buộc}.
*Tiêu chí chấp nhận:* các câu lệnh mẫu ("đưa pallet A tới chuyền 3, tránh người") tạo ra kế hoạch hợp lệ; khớp tên vật **không phân biệt hoa/thường, dấu**.

### F2 — Lập kế hoạch nhiều bước + tự replan
Agent sinh chuỗi hành động, thực thi từng bước, **quan sát**, và **replan** khi bị chặn; có **cap** số bước/replan chống treo.
*Tiêu chí chấp nhận:* kịch bản "người chắn lối" → agent đổi kế hoạch và vẫn giao thành công; vượt cap → dừng có kiểm soát (`status=failed`).

### F3 — Minh bạch + human‑in‑loop
Hiển thị **kế hoạch** (đánh dấu bước đang chạy/đã xong) và **trace** *node → tool(args) → observation → ✓/✗*; nhãn **grounded**; nút **⤓ Xuất audit log (JSON)**. Gặp người sát/bất định → **DỪNG & HỎI** (badge + panel trả lời).
*Tiêu chí chấp nhận:* mỗi hành động có 1 dòng trace; audit log tải về đầy đủ các bước + metric.

### F4 — Biết "nói không" (infeasible)
Khi vật không tồn tại hoặc mục tiêu bất khả thi, agent **báo không làm được**, không bịa kết quả.
*Tiêu chí chấp nhận:* task infeasible → agent kết luận đúng là không khả thi.

### F5 — Showcase chống "bể" (replay) + đa năng lực
Chế độ **▶ Xem demo (phát lại)** chạy bản ghi thật, **không cần API/quota/mạng**; các chip 1‑chạm minh hoạ từng năng lực (giao/replan/an toàn/nói‑không); fallback sang demo khi Gemini quá tải.
*Tiêu chí chấp nhận:* mở web, bấm 1 chip → chạy ngay; mất mạng vẫn demo được.

### F6 — Bằng chứng đo lường (eval)
Harness chạy bộ task, tính các chỉ số, xuất `report.md`, **tách bạch** Bảng A (agent Gemini thật) với Bảng B (mock A* kiểm môi trường).
*Tiêu chí chấp nhận:* report nêu rõ **n**, công thức success, và disclosure giới hạn.

---

## 7. Trải nghiệm chính (UX)

Một trang web tối giản, dark mode, responsive (laptop + điện thoại): cột trái là **canvas kho 2D** (robot, pallet, người, vật cản, khu vực) + chú giải; cột phải là các panel **Kế hoạch / Trace / Chỉ số / Hỏi người / Kết quả**. Badge trạng thái lớn (CHƯA CHẠY → ĐANG LẬP KẾ HOẠCH → ĐANG CHẠY → BỊ CHẶN→REPLAN → DỪNG·HỎI → HOÀN THÀNH/THẤT BẠI). Hai lối vào rõ ràng: **Xem demo (khuyên dùng)** và **Chạy thật (Gemini)**.

---

## 8. Chỉ số thành công (số liệu trung thực)

> Nguồn duy nhất: [`eval/results/report.md`](eval/results/report.md). Công thức: `success_rate = task done / task feasible`, luôn kèm **n**.

| Chỉ số | Kết quả (agent Gemini thật) | Mục tiêu | Ghi chú |
|---|---|---|---|
| success_rate — 7 task lõi (5 nhóm) | **100% ± 0%** | ≥90% | basic/obstacle/pick‑drop/language/replan |
| success_rate — tổng | **87.5%** (n=8) | ≥90% | 1 task safety = *asking* (đúng hành vi) |
| latency/bước | **4.44s ± 2.66s** | <3s | ⚠️ **chưa đạt** — báo thật |
| invalid_tool_calls | 0.0% | <5% | — |
| infeasible_correct | 100% | >90% | agent biết "nói không" |
| safety_events_handled | **3** | >0 | agent **chủ động dừng/hỏi** khi gặp người |
| replan ablation (ON/OFF) | **12/19 → 19/19** | — | **trên harness A\* xác định — *chưa* chạy trên LLM agent** |

> **n=8** là số lần chạy agent thật thành công (free‑tier Gemini 20 req/ngày). Đây là mẫu nhỏ, công bố rõ. `safety_violations=0` là do **sim chặn cứng** (không phải phép đo an toàn), nên **không** dùng làm headline.

---

## 9. Ràng buộc & Giả định

- Thời lượng ~2 tuần, chỉ laptop, **không phần cứng**; LLM dùng **Gemini free‑tier** (giới hạn quota).
- Thế giới là **mô phỏng 2D có thẩm quyền ở backend** (Python) để logic kiểm thử được.
- Giả định: vận hành viên ra lệnh ngắn gọn, một mục tiêu/lần; môi trường vừa phải (grid ~16×10).

---

## 10. Rủi ro & Giảm thiểu

| Rủi ro | Giảm thiểu |
|---|---|
| LLM chậm/hết quota khi demo | Chế độ **phát lại** bản ghi thật; cap bước; cache; nhãn "đang quá tải → Demo nhanh" |
| Agent lệch/treo | Cap `max_steps`/`max_replans` → `failed` có kiểm soát; fallback `ask_human` |
| Hiểu nhầm "an toàn thật" | Phát biểu rõ: an toàn do **sim chặn cứng**; chỉ khoe `safety_events_handled` |
| Mẫu eval nhỏ (n=8) | Công bố n minh bạch; script `run_multiseed.py` để chạy thêm khi có quota |
| Khoảng cách sim‑to‑real | Định vị rõ phạm vi; lộ trình nối ROS/perception ở bản sau |

---

## 11. Lộ trình

- **Ngắn hạn:** deploy live URL (Render); chạy đủ 19 task × nhiều seed trên Gemini; quay video demo; thu ≥3 feedback người dùng thật.
- **Trung hạn:** nối `move/pick` vào **ROS + perception camera** (tái dùng code CV cũ làm tool tri giác).
- **Dài hạn:** RAG "thư viện kỹ năng/quy trình" kho; đa robot; fusion lớp an toàn LiDAR.

---

## 12. Câu hỏi mở / Quyết định cần chốt

- Có nâng `n` agent thật (chạy 19×3 trên paid tier ~$0.12) trước hạn nộp không?
- Hướng giảm latency: cache plan / chỉ gọi LLM khi replan / model nhanh hơn — chọn cái nào để báo có số?
- Điền MSSV thành viên còn thiếu; thu feedback người dùng thật (đang trống — **không bịa**).

---

## 13. Trung thực & Disclosure (giữ nguyên, đừng gỡ)

Showcase ghi rõ **"thế giới mô phỏng · agent thật"**; eval tách **Bảng A (agent Gemini thật)** với **Bảng B (mock A*)**; thừa nhận latency ~4.4s/bước và mẫu nhỏ; nhãn ablation đúng engine ("harness A\* xác định — chưa chạy trên LLM agent"). Đây là **điểm tin cậy**, không phải điểm yếu cần che.
