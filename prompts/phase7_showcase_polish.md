# Prompt cho Claude Code — PHASE 7 (Showcase chứng minh ĐỦ tiêu chí Agent + tính ứng dụng)

> Dán vào Claude Code. Showcase (RoboPlanner) đã **chạy ổn** rồi — đừng làm lại phần đó. Phase 7 chỉ để showcase **chứng minh đủ năng lực agent** (không chỉ replan) và **kể được tính ứng dụng**.

## Đã tốt (GIỮ NGUYÊN, không sửa)
Free‑text + voice → "Chạy thật" (agent thật, lệnh tùy ý); hero replay; 429/timeout → panel gợi ý Demo nhanh; panels Kế hoạch/Trace/Hỏi/Kết quả; hero scenario tự nạp; badge "thế giới mô phỏng · agent thật".

## Vấn đề cần xử (đã soi từ code)
1. **Showcase mới chứng minh ~1 năng lực (replan).** Chỉ 1 chip + 1 replay → judge chủ yếu thấy mỗi replan. Tiêu chí agent rộng hơn: hiểu lệnh NL · lập kế hoạch giao‑nhận · né vật cản · **dừng/hỏi an toàn** · **biết "nói không" khi bất khả thi**.
2. **Tính ứng dụng chưa được kể trên sản phẩm.** Landing không nói rõ "dùng ở đâu, cho ai, lợi gì".
3. **Free‑text "Chạy thật" dễ fail live** nếu judge gõ vật/zone không tồn tại trong kịch bản.

```
NHIỆM VỤ PHASE 7:

1) ĐA NĂNG LỰC — thêm 3–4 CHIP lệnh mẫu, mỗi chip kèm caption "minh hoạ năng lực gì":
   - 📦 Giao cơ bản: "Đưa pallet A tới chuyền 3"            → lập kế hoạch + pick/drop
   - 🚧 Replan (hero): "...tránh người" (đã có)             → tự lập lại kế hoạch khi bị chặn
   - 🛑 An toàn: lệnh dẫn robot tới người sát               → agent DỪNG & HỎI (human-in-loop)
   - ⛔ Bất khả thi: "Lấy thùng Z" (không tồn tại)          → agent BIẾT NÓI KHÔNG, không bịa
   Mỗi chip set goal-input (+ đổi scenario phù hợp nếu cần).

2) REPLAY ĐA NĂNG LỰC — ghi thêm 1–2 fixture replay THẬT (như hero): một cho "an toàn dừng/hỏi",
   một cho "bất khả thi nói không". Lưu frontend/replays/*.json. Cho chọn replay nào (nút/dropdown):
   hero / an toàn / bất khả thi — mỗi cái hiện caption "đang phát lại: <năng lực>".
   Nhãn trung thực: "bản ghi THẬT của agent, không gọi lại API". (Replay an toàn: caption rõ
   "agent dừng & hỏi là ĐÚNG — không cố đi tiếp", không trình bày như giao hàng thành công.)

3) TÍNH ỨNG DỤNG (landing) — thêm 1 khối "Ứng dụng" GỌN (1–2 câu):
   "Robot vận chuyển kho VinFast: vận hành viên ra lệnh bằng tiếng Việt thay vì lập trình từng
   bước; agent tự xử lý khi môi trường đổi (người/vật cản); trace minh bạch để audit an toàn."

4) GỢI Ý VẬT/ZONE cạnh ô input (từ currentState): hiện "Trong kho: pallet A, thùng B · Khu:
   chuyền 3, khu A" → judge gõ lệnh agent làm được. Thêm 1 dòng nhỏ: "Vật không có → agent sẽ
   báo không làm được" (biến rủi ro fail thành điểm: đúng tiêu chí 'biết nói không').

5) ỔN ĐỊNH:
   - Đảm bảo StaticFiles phục vụ `/replays/*.json`. Replay 404 → thông báo nhẹ, vẫn cho "Chạy thật".
   - (Tùy chọn) WS đứt giữa chừng → thử reconnect 1 lần rồi mới fallback quota panel.

RÀNG BUỘC: không phá Phase 0–6; pytest+ruff xanh; escape text vào innerHTML; replay là bản ghi
THẬT có nhãn; không commit secret.

DoD:
- ≥3 chip + ≥2 replay phủ: giao / replan / an toàn / bất‑khả‑thi; mỗi cái caption "minh hoạ gì".
- Landing có khối "Ứng dụng" ngắn + gợi ý vật/zone cạnh input.
- Demo nhanh chọn được replay theo năng lực; tất cả không tốn quota; /replays phục vụ OK.
- 429 / replay‑404 không crash; /health ok.
- pytest+ruff xanh. Xong DỪNG, báo: chip & replay nào, ảnh landing + 1 ảnh mỗi replay.
```

---

> Sau phase này, khi BTC mở app: thấy ngay **agent giải đủ kiểu tác vụ** (giao, replan, dừng‑hỏi, nói‑không) + hiểu **dùng để làm gì** — đúng yêu cầu "show đúng tiêu chí Agent xử lý được & ứng dụng được", mà vẫn chạy chắc nhờ replay.
