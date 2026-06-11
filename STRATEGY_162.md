# CHIẾN LƯỢC 162 — Agent lập kế hoạch tác vụ · Ăn trọn rubric 50đ

> **Sản phẩm (1 câu):** Vận hành viên ra **mục tiêu bằng tiếng Việt** → agent (LLM) **tự lập kế hoạch nhiều bước**, thực thi trong **kho mô phỏng 2D** bằng tool, **tự replan** khi gặp người/vật cản — minh bạch, có người trong vòng lặp.
>
> **Vì sao thắng:** đây là **agent đúng nghĩa** (vòng reason→plan→act→observe→replan + tool‑calling) — đúng thứ rubric BTC cho điểm cao; demo trọn trên laptop; tái dùng được perception CV cũ làm tool.
>
> **Trạng thái:** Phase 0 ✅ (World + A* + schema + render + 27 test, ruff sạch). Tài liệu này là kim chỉ nam để **không chỉ qua vòng (35/50) mà nhắm 45+/50**.

---

## 0. Tư duy chốt: dồn lực vào nơi Cohort 1 chết

Phân tích 12 đội Cohort 1 (xem `docs/guide/anti-patterns/cohort-1-mistakes.md`): điểm thấp nhất tập trung ở **DevOps** và **Code Quality**, và **bằng chứng đánh giá (Eval)**:

- **CI/CD: 0/12 đội có.** → Chỉ cần CI xanh là vượt mặt 100% Cohort 1 ở mục này.
- **Test: chỉ 2/12 đội có.** → Ta đã có 27 test từ Phase 0.
- **Eval evidence: chỉ 2/12 đội có.** → Bộ task + ablation là **đòn khác biệt**.
- **Architecture diagram: 5/12 thiếu** → mất 2–3đ System. Ta có sẵn 3 sơ đồ Mermaid.

> **Chiến lược điểm:** sản phẩm (agent) vốn đã "đúng chất" → đừng để mất điểm ở mấy mục **kỹ thuật cơ bản** mà Cohort 1 bỏ quên. Mỗi mục đó là điểm "miễn phí" nếu làm kỷ luật.

---

## 1. Rubric 50đ → nước đi ăn điểm

BTC chấm **5 tiêu chí × 10đ**. Tối thiểu qua vòng = 35/50. Mục tiêu của ta = **45+/50**.

| Tiêu chí | BTC muốn gì | Nước đi để chạm 9–10 | Bằng chứng (deliverable) | Mục tiêu |
|---|---|---|---|---|
| **Product / Business** | Vấn đề thật, có người dùng, có số đo, feedback | Câu chuyện "vận hành viên ra lệnh tiếng Việt"; 3 pain rõ; **before/after**; bảng metric + ≥3 feedback | README, `eval/results/report.md`, video | **9** |
| **System Design** | Kiến trúc rõ, diagram, cấu trúc thư mục | LangGraph plan→act→observe→**replan**; sim "có thẩm quyền" ở backend; **3 sơ đồ Mermaid**; state schema tường minh; cap loop | `ARCHITECTURE.md`, `docs/architecture_diagram.md`, `src/` | **9–10** |
| **UX / UI** | Responsive, dark mode, accessibility | Canvas 2D gọn đẹp; **bảng trace "suy nghĩ→tool→observation"**; badge DỪNG/HỎI; chạy mượt **laptop + điện thoại**; (stretch) **voice tiếng Việt** | `frontend/`, video | **9** |
| **DevOps** | Docker, CI/CD, logging, .env | **CI xanh** (ruff+pytest+build) — vượt 100% Cohort 1; **LangSmith + AI‑log hook**; deploy **Render/Railway + Vercel**; `.env` sạch; `/health` | `.github/workflows/ci.yml`, `Dockerfile`, Live URL | **9–10** |
| **Code Quality** | Type hints, naming, tests, không bare except | Type hints toàn bộ; **pytest từng tool + graph**; **không bare except**; hàm ngắn; Pydantic schema; **test bất biến "không hallucinate"** | `src/`, `tests/`, ruff | **9–10** |

> **Eval xuyên suốt:** không phải tiêu chí riêng nhưng **nuôi điểm Product + System + Code**. Đây là chỗ ta tạo cách biệt rõ nhất với mọi đội khác.

---

## 2. Bài học Cohort 1 → checklist phản đòn (mỗi lỗi = 1 điểm cần giữ)

| # | Lỗi Cohort 1 | Phản đòn của ta |
|---|---|---|
| 1 | Bare except (3/12) | Bắt exception cụ thể + log; ruff rule chặn `E722` |
| 2 | Hardcode secret (1/12) | `GEMINI_API_KEY` chỉ ở `.env`; `.env` trong `.gitignore` |
| 3 | Không test (10/12) | pytest từng tool/world/graph; **đã có 27 test** |
| 4 | **Không CI/CD (12/12)** | `.github/workflows/ci.yml` chạy ruff+pytest+build mỗi push → **badge xanh trên README** |
| 5 | Hàm quá dài | Mỗi node/tool 1 việc, ≤ ~30 dòng; tách `World` mutation riêng |
| 6 | Thiếu diagram (5/12) | 3 sơ đồ Mermaid (system / agent loop / tool layer) render trên GitHub |
| 7 | README kém (6/12) | Problem→Solution→Stack→Setup→Team + badges + bản đồ deliverable |
| 8 | Không eval (10/12) | Bộ 15–20 task + metric tự động + **ablation replan** |
| 9 | Code 1 file (4/12) | Cấu trúc `src/agents|services|api|models` rạch ròi |
| 10 | Không type hints | Type hints + `ruff` + (tuỳ) `mypy` |

---

## 3. Định vị sản phẩm (đẩy Product → 9)

**Vấn đề:** điều khiển robot kho hôm nay phải lập trình từng bước, cứng nhắc khi môi trường đổi.

**3 pain → agent giải:**

1. *Vận hành viên (không phải kỹ sư)* không ra lệnh cho robot được → **ra lệnh tiếng Việt tự nhiên** (161).
2. *Quản lý vận hành* gặp môi trường động (người/vật cản) phải lập trình lại tay → agent **tự lập kế hoạch + replan** (162).
3. *An toàn/QA* sợ "hộp đen" → **minh bạch**: hiện kế hoạch + trace; gặp người → **dừng/hỏi**.

**Câu chuyện ăn điểm (kể thẳng với giám khảo):** đội từng làm bản CV (#163), **tự đánh giá trung thực thấy "chưa phải agent"** (chỉ tri giác + 1 lời gọi VLM, không có vòng lập kế hoạch/tool‑calling) → **pivot sang 162** và **tái dùng perception cũ làm tool tri giác**. Đây vừa là **moat minh bạch**, vừa cho thấy năng lực **tự phản tỉnh** mà rubric đánh giá cao.

---

## 4. Brainstorm — đẩy từng tiêu chí lên kịch trần

### 4.1 Product/Business (≥9)
- **Demo kịch bản tiếng Việt** sống động: *"Đưa pallet A từ khu A sang chuyền 3, tránh người."*
- **Before/after**: lập trình tay (cứng) ↔ agent (ra lệnh ngôn ngữ + tự sửa).
- **Bảng metric** (success rate, 0 safety violation) hiện ngay trên UI → "có số, không chém".
- **≥3 feedback** từ người **không kỹ thuật** thử ra lệnh thành công (mạnh nhất về mặt sản phẩm).
- "**3 bằng chứng sản phẩm thật**": (1) URL công khai mở trên điện thoại; (2) AI thật (LLM lập kế hoạch + tool thật); (3) số đo trên bộ task.

### 4.2 System Design (≥9–10)
- **LangGraph** plan‑and‑execute + ReAct: `parse_goal→perceive→plan→act→observe→replan→summarize`, có **cap steps/replans** chống treo.
- **Sim "có thẩm quyền" ở backend** (Python `World`) → tool đọc **observation thật**, logic **testable**.
- **3 sơ đồ Mermaid** + **state schema** tường minh trong doc.
- **WebSocket** stream trace + trạng thái → kiến trúc realtime rõ ràng.

### 4.3 UX/UI (≥9)
- Canvas 2D gọn, **dark mode**, **responsive** (test thật trên điện thoại).
- **Bảng trace** 3 cột *suy nghĩ → tool gọi → observation* — vừa đẹp vừa chứng minh "agent thật".
- **Badge an toàn DỪNG/HỎI** khi gặp người; nút **kịch bản mẫu 1‑chạm**.
- **Accessibility**: tương phản đạt WCAG AA, `aria-label`, điều hướng bàn phím.
- (Stretch) **Nhập mục tiêu bằng giọng nói tiếng Việt** (Web Speech API) — ấn tượng, chi phí thấp.

### 4.4 DevOps (≥9–10) — đòn bẩy lớn nhất
- **Docker** chạy 1 lệnh; **CI xanh** (ruff + pytest + docker build) → **badge** trên README.
- **AI logs**: bật **LangSmith** + hook `AI_LOG_*` (deliverable #4) — log prompt + tool call.
- **Deploy**: backend **Render/Railway** (Docker), frontend tĩnh kèm theo hoặc **Vercel**; có `/health`.
- **Secrets an toàn**: `.env` (gitignored), `.env.example` không chứa key thật của cá nhân.
- (Tuỳ) **uptime/ghi log request** đơn giản để có "bằng chứng vận hành".

### 4.5 Code Quality (≥9–10)
- **Type hints** toàn bộ; `ruff` xanh; hàm ngắn, một việc.
- **pytest từng tool + world + graph**; giữ **27 test Phase 0** xanh.
- **Không bare except**; validate input bằng **Pydantic**.
- **Test bất biến "không hallucinate"**: kiểm chứng mọi tool trả observation **khớp** trạng thái `World` thật (không bịa).

### 4.6 Evaluation (điểm khác biệt)
- **Bộ 15–20 task** (bản đồ + mục tiêu + lời giải khả thi, JSON trong `eval/`).
- **Metric tự động (pytest)**: `success_rate`, `safety_violations` (**= 0**), `avg_steps`, `replan_count`, `invalid_tool_calls`, độ trễ/bước.
- **Ablation**: agent **có replan** vs **không replan** → định lượng giá trị vòng observe→replan (kỳ vọng: có replan ↑ success ở task bị chặn). **Đưa biểu đồ này lên slide.**
- Auto‑export `eval/results/report.md` (đúng deliverable #10).

### 4.7 Ý tưởng "WOW" cho giám khảo (chọn 1–2, đừng ôm hết)
1. **Biểu đồ ablation** replan vs no‑replan — bằng chứng "vòng lặp agent có giá trị".
2. **0 lần đi xuyên người** — badge an toàn + metric live (kể chuyện "human‑in‑loop").
3. **Voice tiếng Việt** — ra lệnh bằng giọng nói, rẻ mà ấn tượng.
4. **Perception bridge**: nạp **1 ảnh kho thật** → OWL‑ViT (code CV cũ) → sinh world state → "**tái dùng, không phí công**".
5. **`ask_human` thật**: khi bất định, agent bật hộp hỏi và chờ người trả lời — minh bạch sống động.
6. **Baseline đối chứng** (scripted, không LLM) để làm nổi giá trị của agent.

---

## 5. Khác biệt ăn điểm (vs Cohort 1 & các đội khác)

- **Agent đúng nghĩa** (vòng plan→act→observe→replan + tool‑calling), không phải "1 lời gọi LLM".
- **Eval + ablation** — thứ 10/12 đội Cohort 1 không có.
- **Minh bạch** (trace + nhãn "thật vs mô phỏng") tạo niềm tin.
- **CI/CD xanh** — vượt 100% Cohort 1.
- **Pivot trung thực** từ CV → agent: câu chuyện trưởng thành kỹ thuật.

---

## 6. Kế hoạch 2 tuần (refined) — mỗi phase ↔ tiêu chí + deliverable

| Phase | Nội dung | DoD | Phục vụ tiêu chí | Trạng thái |
|---|---|---|---|---|
| **0** | World sim 2D + A* + schema + render | Mở web thấy kho 2D, nạp bản đồ mẫu | System, Code | ✅ **Done (05/06)** |
| **1** | 9 tool thao tác World + pytest | Gọi move/pick/drop thấy robot đổi; tool có test | Code, System | ⏳ tiếp theo |
| **2** | LangGraph plan loop + Gemini + stream trace | Mục tiêu đơn giản → agent tự xong, hiện kế hoạch+trace | System, Product | ⏳ |
| **3** | Replan + an toàn (ask_human/wait) + cap loop | Người chắn lối → đổi kế hoạch; 0 đi xuyên người | System, Product | ⏳ |
| **4** | UI/UX responsive + dark + bảng trace (+voice) | Demo mượt laptop + điện thoại | UX/UI | ⏳ |
| **5** | Eval + deploy + 6 form + video + pitch | 10 deliverable đủ; demo 3 phút × 3 lần không lỗi | DevOps, Product, tất cả | ⏳ |

---

## 7. Bản đồ 10 deliverables → vị trí · trạng thái · phụ trách

| # | Deliverable | Ở đâu | Trạng thái | Chính |
|---|---|---|---|---|
| 1 | Source Code | `src/` | 🔄 Phase 0 xong | Đạt/Thái |
| 2 | README | `README.md` | ✅ (162) | Thái |
| 3 | Architecture | `ARCHITECTURE.md`, `docs/architecture_diagram.md` | ✅ (162) | Thái |
| 4 | AI Logs | LangSmith + hook `AI_LOG_*` | ⏳ bật ở Phase 2 | Đạt |
| 5 | Live URL | Render/Railway + Vercel | ⏳ Phase 5 | Đạt |
| 6 | Video Demo (≤5') | YouTube/Drive | ⏳ Phase 5 | Mạnh |
| 7 | Pitch Deck (10 slide) | `presentation/` | ⏳ Phase 5 | Mạnh |
| 8 | Journal | `JOURNAL.md` | ✅ cập nhật | cả nhóm |
| 9 | Worklog | `WORKLOG.md` | ✅ cập nhật | cả nhóm |
| 10 | Eval Evidence | `eval/results/report.md` | 🔄 khung sẵn, số sau | Mạnh |

---

## 8. Rủi ro & dự phòng

| Rủi ro | Dự phòng |
|---|---|
| Deploy lỗi giờ chót | Quay sẵn **video demo**; chạy local + ngrok; build Docker test trước 1 ngày |
| Mất mạng khi demo | **Kịch bản nạp sẵn** từ JSON; cache; có ảnh/clip dự phòng |
| LLM chậm/giới hạn quota | Gemini free tier + **cap steps**; cache plan; stream để cảm giác nhanh |
| Agent lệch/treo | Cap `steps`/`replans`; fallback `ask_human`; baseline scripted |
| Ôm đồm stretch (voice/perception) | Chỉ làm **sau** khi 5 phase lõi xanh |

---

## 9. Quyết định cần chốt NGAY (trước Phase 2)

1. **LLM = Gemini** (đúng PLAN + README). → Cập nhật `src/config.py` (`gemini_api_key`, `model_name="gemini-flash-latest"`), `requirements.txt` (`langchain-google-genai` thay `langchain-openai`), `.env`. *(`.env.example` đã sửa sang Gemini.)*
2. **Người = vật cản ĐỘNG**: `move_to` đi từng ô, **dừng khi ô kế có người** (đừng để A* tự vòng tránh) — để kích hoạt đúng vòng dừng/hỏi/replan ở Phase 3. *(Chi tiết trong `prompts/phase1_tools.md`.)*
3. **Deploy**: backend **Render/Railway** (Docker) + frontend (kèm static hoặc **Vercel**). Dựng skeleton deploy sớm để tránh nghẽn Phase 5.
4. **Eval sớm**: chốt **15–20 task** ngay khi xong Phase 2 để có số cho slide (đừng để dồn cuối).

---

## Phụ lục — điểm mạnh đang có (Phase 0)

`World` grid 16×10 + **A\*** (có test edge case: goal bị chặn / không đường / start≡goal); schema `Cell/Entity/Zone/WorldState` (Pydantic, round‑trip); API `GET /world` + `POST /scenario`; frontend canvas render + badge "thế giới mô phỏng · agent thật"; **27 test xanh, ruff sạch**. 2 kịch bản (basic + blocked — người đã đặt sẵn cạnh tường để demo replan).

> Tài liệu liên quan: `PLAN_agent_taskplanner.md` (scoping chi tiết), `prompts/phase1_tools.md` (prompt build Phase 1), `WORKLOG.md` / `JOURNAL.md` (tiến độ).
