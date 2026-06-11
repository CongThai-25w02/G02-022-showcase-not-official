# Prompt cho Claude Code — REBUILD SHOWCASE (#162, đúng chủ đề BTC)

> Dán vào Claude Code. **Dùng file này THAY cho `phase7_showcase_polish.md`.**
> Mục tiêu: showcase robot kho **#162 (đúng chủ đề BTC robotics)** nhưng khi mở ra **chứng minh rõ 3 điều**: (1) **Agent xử lý được** đa dạng tác vụ, (2) **Ứng dụng được** (use‑case kho thật + lộ trình tới robot thật), (3) **Đáng tin / kiểm chứng được** (mỗi hành động grounded từ trạng thái thật, có trace audit) — đây là phần "agent kiểm chứng" làm sản phẩm khác biệt, vẫn nằm trong khuôn khổ robot.
>
> KHÔNG làm slide/video lần này. KHÔNG xây lại backend/agent/eval đang chạy tốt — chỉ **nâng cấp showcase UX + framing + bằng chứng**.

## Giữ nguyên (đang tốt — đừng phá)
Agent LangGraph + Gemini + World + eval (Bảng A/B) · WS live‑run cho lệnh tùy ý · replay hero · 429/timeout fallback · voice · panels Kế hoạch/Trace/Hỏi/Kết quả · 72 pytest xanh.

```
NHIỆM VỤ — nâng showcase theo 3 trục:

=== TRỤC 1: "AGENT XỬ LÝ ĐƯỢC" (đa năng lực, không chỉ replan) ===
1. Thêm 3–4 CHIP lệnh mẫu, mỗi chip 1 năng lực + caption "minh hoạ gì":
   📦 Giao cơ bản · 🚧 Replan khi người chắn (hero) · 🛑 An toàn: dừng & hỏi · ⛔ Bất khả thi: biết nói không.
   Mỗi chip set goal-input (+ đổi scenario phù hợp nếu cần).
2. Ghi thêm 1–2 REPLAY THẬT (an toàn dừng/hỏi; bất khả thi nói không) lưu frontend/replays/*.json;
   nút Demo nhanh chọn được replay theo năng lực, caption rõ "đang phát lại: <năng lực>".
   (Replay an toàn: caption "agent dừng & hỏi là ĐÚNG", không trình bày như giao thành công.)

=== TRỤC 2: "ĐÁNG TIN / KIỂM CHỨNG ĐƯỢC" (điểm khác biệt cốt lõi) ===
3. Mỗi dòng TRACE hiển thị rõ: node → tool(tham số) → **QUAN SÁT THẬT TỪ WORLD** → quyết định.
   Thêm nhãn nhỏ mỗi bước: "✓ grounded — đọc trạng thái thật, không bịa" (vì tool đọc World thật).
4. Nút **"⤓ Xuất audit log"**: tải toàn bộ trace của lần chạy (JSON: từng bước + observation thật +
   plan + replan + kết quả) → bằng chứng "agent audit được" cho người vận hành/đội an toàn.
5. 1 ô chỉ số nhỏ sau khi chạy: "tool calls: N · grounded: 100% · hallucinated: 0 · replan: k"
   (đọc từ chính history của lần chạy đó — không hardcode).

=== TRỤC 3: "ỨNG DỤNG ĐƯỢC" (đúng chủ đề + thật thà) ===
6. Khối "Ứng dụng" gọn trên landing (1–2 câu): "Robot vận chuyển kho VinFast — vận hành viên ra
   lệnh tiếng Việt thay vì lập trình; agent tự xử lý khi môi trường đổi; trace minh bạch để audit an toàn."
7. Khối "Lộ trình tới robot thật" (1 dòng, trung thực): "Bản này chứng minh lớp NGÔN NGỮ→KẾ HOẠCH→
   KIỂM CHỨNG trong mô phỏng; bản sản xuất nối tool move/pick vào ROS + perception camera thật."
   (Vừa đúng chủ đề robotics, vừa thừa nhận đây là sim — không overclaim.)
8. Gợi ý vật/zone hiện có cạnh ô input (từ currentState): "Trong kho: pallet A… · Khu: chuyền 3…";
   thêm "Vật không có → agent báo không làm được" (biến rủi ro fail thành đúng tiêu chí).

=== ỔN ĐỊNH ===
9. StaticFiles phục vụ /replays/*.json; replay 404 → thông báo nhẹ, vẫn Chạy thật được.
10. (Tùy chọn) WS đứt giữa chừng → thử reconnect 1 lần rồi mới fallback quota panel.

RÀNG BUỘC: không phá Phase 0–6; pytest+ruff xanh; escape text; replay là bản ghi THẬT có nhãn;
không commit secret. GIỮ đúng chủ đề robot #162 — KHÔNG đổi sang domain doanh nghiệp.

DoD:
- Mở app → thấy ngay agent giải **≥4 kiểu tác vụ** (giao/replan/an toàn/nói‑không) qua chip + replay.
- Trace mỗi bước có nhãn "grounded"; có nút **Xuất audit log** (JSON tải được); ô chỉ số grounded/hallucinated.
- Landing có khối **Ứng dụng** + **Lộ trình tới robot thật** (trung thực) + gợi ý vật/zone.
- Demo nhanh không tốn quota; 429/replay‑404 không crash; /health ok.
- pytest+ruff xanh. Xong DỪNG, báo: chip/replay nào, ảnh landing + ảnh trace có nhãn grounded + audit log mẫu.
```

---

> **Vì sao bản này mạnh hơn:** vẫn 100% đúng chủ đề #162 (robot kho), nhưng phô đúng thứ giám khảo *và* nhà đầu tư cần thấy — agent **giải được nhiều kiểu việc**, **kiểm chứng được** (grounded + audit log, không hallucinate), và **có đường ra robot thật**. Đây là cách "cứu" giá trị hướng A mà không rời cuộc thi.
