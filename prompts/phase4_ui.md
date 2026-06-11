# Prompt cho Claude Code — PHASE 4 (Wire UI ↔ Agent: animation + trace + safety badge)

> Dán nguyên khối dưới đây vào Claude Code (mở trong repo `C2-App-022`).
> **Lý do Phase 4 quan trọng:** backend agent (Phase 0–3) đã chạy + có test, **nhưng `frontend/app.js` vẫn là bản Phase 0** — nút "Chạy" mới chỉ hiện chữ "sẽ có ở Phase 2", chưa gọi agent, chưa animate, chưa hiện trace. Không có Phase 4 thì **không có demo nhìn được trên trình duyệt**.

---

```
Bối cảnh: repo C2-App-022, đề tài AI20K-162 (agent lập kế hoạch điều khiển robot kho bằng
ngôn ngữ tự nhiên). Backend đã xong Phase 0–3: World sim + 9 tool + LangGraph (parse→perceive→
plan→act→observe→replan→summarize) + Gemini + replan/safety + người động. Đọc ARCHITECTURE.md
và PLAN_agent_taskplanner.md. CHỈ LÀM PHASE 4 — nối UI vào agent + minh bạch trace + an toàn.

Hợp đồng API hiện có (KHÔNG đổi nghĩa, chỉ bổ sung):
- POST /api/v1/run {goal_text} -> {plan, history, answer, status}
- WS /api/v1/ws : client gửi {"goal_text": "..."} ; server stream:
    {"type":"step","node":..,"last_action"?:{...},"world_view"?:{...},"status"?:..,"plan"?:[...],"answer"?:..}
    rồi {"type":"done"} hoặc {"type":"error","detail":..}
- AgentState: goal_text, goal, plan[list], history[list of {action,args,observation,ok}],
  world_view, status (planning|acting|blocked|asking|done|failed), replans, steps, answer, pending_question.
- World là singleton (get/set_current_world) bị mutate khi agent chạy.

NHIỆM VỤ PHASE 4:

A) Backend (nhỏ — để UI animate được):
   1. Trong WS step event, THÊM trường "world": snapshot gọn của World hiện tại sau bước đó —
      tối thiểu {robot:{pos,carrying}, people:[{id,pos}], tick}. (Dùng get_current_world().to_state()
      hoặc một hàm to_snapshot() gọn.) Mục đích: frontend vẽ robot/người di chuyển từng bước.
   2. Giữ nguyên POST /run và GET /world. Nếu thêm to_snapshot() thì có unit test nhỏ.

B) Frontend (frontend/app.js, index.html, style.css) — viết lại phần điều khiển (giữ hàm drawWorld
   đã có, mở rộng để nhận snapshot từng bước):
   1. Nút "Chạy": mở WebSocket tới /api/v1/ws, gửi {goal_text}; disable nút khi đang chạy,
      enable lại khi {type:"done"|"error"}.
   2. ANIMATE: mỗi step event có "world" → cập nhật vị trí robot/người rồi redraw (drawWorld).
      Chèn delay nhỏ (vd 250–400ms/bước) để mắt theo kịp; không chặn UI.
   3. PANEL KẾ HOẠCH: khi nhận "plan" → render danh sách bước (numbered); làm nổi bước đang chạy
      (theo steps/last_action nếu suy ra được).
   4. PANEL TRACE (minh bạch — điểm nhấn): mỗi step append 1 dòng "node → action(args) → observation
      [ok/✗]" lấy từ last_action; auto-scroll; ESCAPE mọi text trước khi chèn (chống XSS).
   5. BADGE TRẠNG THÁI theo status: acting="ĐANG CHẠY"(xanh) · blocked="BỊ CHẶN → REPLAN"(vàng) ·
      asking="DỪNG · HỎI NGƯỜI"(đỏ) · done="HOÀN THÀNH"(xanh lá) · failed="THẤT BẠI"(đỏ).
      Khi asking và có pending_question → hiện câu hỏi + ô trả lời (tối thiểu nút "Tiếp tục").
   6. Kết thúc: hiện "answer" (tóm tắt) ở panel kết quả.
   7. Giữ badge minh bạch sẵn có: "thế giới mô phỏng · agent thật".
   8. Responsive + dark: trên màn hình hẹp (điện thoại) canvas + panel kế hoạch/trace xếp dọc;
      nút bấm đủ to. Xử lý WS lỗi/đứt kết nối (hiện thông báo, enable lại nút).

C) (Stretch, nếu kịp) Voice tiếng Việt: nút 🎤 dùng Web Speech API (lang="vi-VN") để đọc mục tiêu
   vào ô input. Có fallback gõ tay nếu trình duyệt không hỗ trợ.

RÀNG BUỘC:
- Frontend vanilla JS (không framework); giữ dark mode; escape text vào innerHTML.
- KHÔNG phá API/agent Phase 0–3; pytest + ruff vẫn xanh.
- Cap nhịp redraw; không leak WebSocket (đóng khi xong/đổi mục tiêu).

DoD PHASE 4 (tự kiểm trước khi báo xong):
- Mở web → chọn kịch bản "warehouse_blocked" → gõ (hoặc nói) mục tiêu tiếng Việt
  (vd "đưa pallet A tới chuyền 3") → bấm Chạy:
  • robot **di chuyển từng bước**; người động cũng cập nhật;
  • panel **kế hoạch** hiện các bước; panel **trace** cuộn theo (node→tool→observation);
  • badge đổi theo trạng thái; gặp người → **DỪNG/HỎI** rồi **replan** đổi đường tới đích;
  • cuối cùng hiện tóm tắt; **0 lần đi xuyên người**.
- Chạy ổn trên khung hình điện thoại (panel xếp dọc).
- `pytest -q` xanh; `ruff check src tests` sạch.

Làm xong Phase 4: liệt kê file đã sửa + ảnh chụp/đoạn mô tả luồng demo + kết quả test, rồi DỪNG
để mình review (chưa sang Phase 5 — eval + deploy).
```

---

**Sau Phase 4** (đã có demo nhìn được), Phase 5 sẽ là: chạy **bộ eval** (`eval/scenarios/SPEC.md`) điền số thật + **ablation có/không replan**, **Docker/deploy** lấy live URL, rồi **video + pitch deck**. Mình (Cowork) làm song song phần eval‑report + deck + deploy runbook trong lúc Claude Code build Phase 4.
