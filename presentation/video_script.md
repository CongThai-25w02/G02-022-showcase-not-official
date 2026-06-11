# Script Video Demo — AI20K‑162 (mục tiêu ~3 phút, tối đa 5)

> **Nguyên tắc quay chắc:** dùng **“▶ Demo nhanh (phát lại)”** làm mạch chính (tức thì, không tốn quota, không bể). Chèn **1 lần “Chạy thật (Gemini)”** ngắn để chứng minh live (nếu mạng ổn). Quay màn hình 1920×1080, giọng đọc rõ, chậm.

> **Chuẩn bị:** mở sẵn `http://localhost:8000` (hoặc live URL) + tab pitch deck ở slide 6 (ablation) và 7 (eval). Pre‑warm app 1 lần. Phóng to canvas cho dễ thấy.

| Thời gian | Hình trên màn hình | Lời đọc (voiceover) |
|---|---|---|
| **0:00–0:18** Hook | Landing app: tiêu đề + kho 2D + chip lệnh mẫu | "Robot vận chuyển trong kho cần hai thứ: hiểu lệnh con người bằng ngôn ngữ thường, và **tự xoay sở khi môi trường thay đổi**. Đây là **AI20K‑162** — một agent làm đúng điều đó." |
| **0:18–0:35** Giải pháp | Trỏ vào ô lệnh + badge "thế giới mô phỏng · agent thật" | "Người vận hành chỉ cần **ra lệnh bằng tiếng Việt**. Agent tự lập kế hoạch, thực thi từng bước trong kho mô phỏng, và **lập lại kế hoạch** khi bị chắn. Mọi suy luận đều minh bạch." |
| **0:35–1:05** Bắt đầu demo | Bấm chip **“đưa pallet A tới chuyền 3, tránh người”** → bấm **▶ Demo nhanh**. Panel **Kế hoạch** hiện ra; robot bắt đầu đi | "Tôi ra lệnh: *đưa pallet A tới chuyền 3, tránh người.* Agent **lập kế hoạch** — các bước hiện bên phải — rồi robot bắt đầu di chuyển, né vật cản." |
| **1:05–1:45** ⭐ Money shot: REPLAN | Người xuất hiện chắn lối → **badge DỪNG/HỎI** đỏ → robot đổi đường (replan) → đi tiếp | "Đúng lúc này — **một người xuất hiện chắn lối**. Agent **không đâm vào**: nó dừng, **quan sát, rồi lập lại kế hoạch** một con đường khác. Đây chính là phần ‘agent’ — tự điều chỉnh, không phải kịch bản cứng." |
| **1:45–2:05** Hoàn thành + trace | Robot tới chuyền 3 → thả pallet → trạng thái **HOÀN THÀNH**. Cuộn panel **Trace** | "Robot giao pallet, hoàn thành. Và toàn bộ **vết suy luận** ở đây: mỗi bước là *suy nghĩ → gọi tool → kết quả thật từ sim* — kiểm chứng được, không bịa." |
| **2:05–2:20** (Tuỳ chọn) chạy thật | Bấm **Chạy thật (Gemini)** cho 1 lệnh ngắn, tua nhanh | "Và đây là agent **chạy thật với Gemini** — chậm hơn vài giây mỗi bước vì là LLM thật, nhưng đúng cùng một hành vi." |
| **2:20–2:45** Bằng chứng | Chuyển sang **slide 6 (ablation)** rồi **slide 7 (eval)** | "Chúng tôi đo trên **agent thật**: 100% trên 5 nhóm lõi (**n=8, sơ bộ**); **0 va chạm là do sim chặn cứng** — chỉ số có nghĩa là agent **chủ động dừng/hỏi**. Ablation cho thấy **trên **harness A* xác định** (chưa chạy trên LLM agent), bật replan nâng **12/19 → 19/19 task**; trên Gemini, node replan thật sự được gọi (avg 0→0.5)** — node replan thật sự chạy. Và chúng tôi **tách bạch** số agent thật với baseline, **thừa nhận giới hạn**: độ trễ, mẫu nhỏ, thế giới mô phỏng." |
| **2:45–3:00** Chốt | Slide 1 / màn team + URL + QR | "AI20K‑162: ra lệnh tiếng Việt, agent tự lập kế hoạch và replan — minh bạch, có người trong vòng lặp. Cảm ơn ban giám khảo." |

## Mẹo quay (chống "bể")
- **Mặc định Demo nhanh** cho đoạn chính → không phụ thuộc mạng/quota, lặp lại y hệt mỗi lần quay.
- Quay **nhiều take ngắn** theo từng hàng bảng rồi ghép; không cần quay liền 3 phút.
- Nếu “Chạy thật” lâu → **tua nhanh 2–4×** đoạn robot đi, giữ nguyên tốc độ ở khoảnh khắc replan.
- Đảm bảo **chữ tiếng Việt rõ** (zoom panel trace/kế hoạch khi nói tới).
- Xuất 1080p, ≤ 5 phút; nhắm **~3 phút**. Upload YouTube/Drive (unlisted) → dán link vào form + README.

## Khớp deliverable
- Video này = **Deliverable #6**. Cấu trúc trùng **pitch deck** (slide 3→demo, 6→ablation, 7→eval) để nhất quán khi thuyết trình.
