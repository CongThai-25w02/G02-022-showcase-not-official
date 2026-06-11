# KẾ HOẠCH CHIA VIỆC — Claude Code × Cowork (tối ưu song song)

> Mục tiêu: build agent 162 trong ~2 tuần, ăn trọn rubric (xem `STRATEGY_162.md`), **không để 2 agent giẫm chân nhau**.

---

## 0. Nguyên tắc tối ưu

1. **Một chủ sở hữu cho `src/`:** **Claude Code** viết toàn bộ code. **Cowork KHÔNG sửa `src/`, `tests/`, `.github/`, `Dockerfile`** → tránh xung đột merge.
2. **Cowork = bộ não kế hoạch + nội dung:** chuẩn bị **prompt chính xác + tiêu chí nghiệm thu (DoD)** cho từng phase, thiết kế eval, viết tài liệu/deck, giữ deliverable map.
3. **Vòng lặp bàn giao:** Cowork ra *prompt + DoD* → Claude Code build & dừng cuối phase → Cowork **review diff + cập nhật docs/eval** → ra prompt phase kế.
4. **Luôn chạy song song:** trong khi Claude Code build phase N (code), Cowork làm phần **không phụ thuộc code** (eval design, pitch, deploy runbook, prompt phase N+1).
5. **Giữ xanh liên tục:** mỗi phase phải `pytest` + `ruff` xanh trước khi sang phase sau (CI gác cổng).

---

## 1. Ai làm gì

| Hạng mục | Claude Code | Cowork (tôi) |
|---|:---:|:---:|
| Code `src/` (world mutation, 9 tools, graph, nodes, api, frontend) | ✅ | — |
| Viết & chạy `pytest` | ✅ | (review chiến lược test) |
| CI/CD, Docker, deploy config | ✅ | runbook + double‑check |
| Chuyển LLM provider → Gemini | ✅ *(step 0 Phase 2)* | ra quyết định + đưa vào prompt |
| **Prompt + DoD từng phase** | — | ✅ |
| **Thiết kế bộ eval** (task set, metrics, ablation) | code chạy số | ✅ thiết kế (`eval/scenarios/SPEC.md`) |
| README / ARCHITECTURE / diagram | — *(đã xong)* | ✅ giữ đồng bộ |
| JOURNAL / WORKLOG | — | ✅ cập nhật mỗi phase |
| `eval/results/report.md` | điền số từ run | ✅ khung + diễn giải |
| **Pitch deck (10 slide)** + video script | — | ✅ |
| Deliverable map + nhắc mốc | — | ✅ |

---

## 2. Lộ trình theo phase — bàn giao & chạy song song

| Phase | Claude Code (code) | Cowork song song | Prompt bàn giao | DoD |
|---|---|---|---|---|
| **1** (đang tới) | 9 tool + World mutation + pytest | Thiết kế eval SPEC; prompt Phase 2 | `prompts/phase1_tools.md` ✅ | tool có test; move/pick/drop đổi World thật |
| **2** | Gemini switch + LangGraph graph/nodes + function‑calling + `POST /run` + `WS /ws` | Pitch skeleton; deploy runbook; prompt Phase 3 | `prompts/phase2_agent_loop.md` ✅ | mục tiêu đơn giản → agent tự xong, hiện kế hoạch + trace |
| **3** | Replan + safety (ask_human/wait) + cap loop | Hoàn thiện eval harness; prompt Phase 4 | `phase3_replan_safety.md` ⏭ | người chắn lối → replan; 0 đi xuyên người |
| **4** | UI responsive + dark + bảng trace (+voice stretch) | Video script; checklist accessibility | `phase4_ui.md` ⏭ | demo mượt laptop + điện thoại |
| **5** | Docker/deploy + chạy eval suite | Điền eval report; pitch final; audit 10 deliverable | `phase5_eval_deploy.md` ⏭ | live URL; demo 3' × 3 lần không lỗi |

---

## 3. Hàng đợi prompt bàn giao (Cowork sản xuất)

- ✅ `prompts/phase1_tools.md`
- ✅ `prompts/phase2_agent_loop.md` *(kèm bước chốt Gemini)*
- ⏭ `prompts/phase3_replan_safety.md` — ra khi Phase 2 gần xong
- ⏭ `prompts/phase4_ui.md`
- ⏭ `prompts/phase5_eval_deploy.md`

> Mẫu mỗi prompt: **Bối cảnh → Ràng buộc (type hints/pytest/ruff/no‑hallucinate) → Việc theo bước → Test bắt buộc → "Xong thì DỪNG để review"**.

---

## 4. Việc Cowork làm NGAY (song song khi Claude Code build Phase 1)

- [x] Kế hoạch chia việc (file này)
- [x] Prompt Phase 2 (`prompts/phase2_agent_loop.md`) — gồm switch Gemini
- [x] Thiết kế bộ eval (`eval/scenarios/SPEC.md`) — 15–20 task + metrics + ablation
- [ ] Pitch deck skeleton (10 slide) — bắt đầu sau khi Phase 2 chạy
- [ ] Deploy runbook (Render/Railway + Vercel)
- [ ] Cập nhật WORKLOG/JOURNAL khi mỗi phase xong

---

## 5. Quy ước tránh xung đột (quan trọng)

- **Cowork chỉ chạm:** `*.md` (docs gốc), `prompts/`, `eval/scenarios/*.md` (spec, **không phải** file code/JSON test), `presentation/`.
- **Claude Code sở hữu:** `src/`, `tests/`, `eval/scenarios/*.json`, `.github/`, `Dockerfile`, `requirements.txt`, `frontend/`.
- **Bàn giao 1 chiều:** Claude Code commit cuối mỗi phase → Cowork review + cập nhật docs → mới ra prompt phase kế (không build song song cùng 1 phase).
- **Quyết định kiến trúc** (vd provider, blocker tĩnh/động) chốt ở `STRATEGY_162.md §9` trước khi code.

---

## 6. Cách bạn (Thái) vận hành mỗi vòng

1. Mở `prompts/phaseN_*.md` → dán vào **Claude Code** → để nó build & dừng.
2. Nó báo "đã làm gì + test gì" → bảo **Cowork** review (dán kết quả hoặc để Cowork đọc repo).
3. Cowork cập nhật WORKLOG/JOURNAL/eval + ra `prompts/phase(N+1)_*.md`.
4. Lặp tới Phase 5 → Cowork ráp pitch + audit deliverable.
