# Checklist nộp bài — AI20K‑162 (trạng thái trung thực)

> Cập nhật: trước hạn nộp. ✅ xong · ⏳ đang/cần làm · ⚠️ cần xác nhận.

## 10 Deliverables BTC

| # | Deliverable | Trạng thái | Việc cần làm |
|---|---|---|---|
| 1 | Source Code (`src/`) | ✅ | 72 pytest + ruff xanh |
| 2 | README.md | ✅ | (đã narrowed + honest) |
| 3 | Architecture Diagram (`docs/architecture_diagram.md`) | ✅ | Mermaid render trên GitHub |
| 4 | AI Logs (LangSmith) | ⚠️ | **Xác nhận key đã set + có trace thật** trên smith.langchain.com (project `ai20k-162`) |
| 5 | **Live URL / Deploy** | ⏳ | Deploy Render theo `DEPLOY_runbook.md` → dán URL vào README + form |
| 6 | **Video Demo** | ⏳ | Quay theo `presentation/video_script.md` (≤5', nhắm 3') → upload → dán link |
| 7 | Pitch Deck (`presentation/pitch_deck.pptx`) | ✅ | (số eval thật) |
| 8 | Weekly Journal (`JOURNAL.md`) | ✅ | đã sync Phase 0–7 |
| 9 | Worklog (`WORKLOG.md`) | ✅ | đã sync Phase 0–7 |
| 10 | Evaluation Evidence (`eval/results/report.md`) | ✅ | Bảng A (agent thật) + B (mock); + `USER_FEEDBACK.md` |

## 5 Tiêu chí chấm (mục tiêu 35+/50)

| Tiêu chí | Min | Tự đánh giá | Để chắc điểm |
|---|---|---|---|
| Product/Business | ≥8 | ⚠️ Khá | **Thu ≥3 feedback** (`eval/USER_FEEDBACK.md`) → điền |
| System Design | ≥7 | ✅ Mạnh | Architecture + LangGraph + folder chuẩn |
| UX/UI | ≥7 | ✅ Tốt | responsive + dark + showcase (replay/trace/audit) |
| DevOps | ≥6 | ✅ Mạnh | Docker + CI + LangSmith + .env |
| Code Quality | ≥7 | ✅ Mạnh | type hints + 72 pytest + ruff, no bare except |

## Việc còn lại (ưu tiên trước nộp)
1. ⏳ **Deploy live URL** (đội, ~10') — `DEPLOY_runbook.md`. Sau đó dán URL vào README + slide 1 + form.
2. ⏳ **Quay video** (đội) — `video_script.md`; dùng **▶ Demo nhanh** cho chắc.
3. ⚠️ **Thu ≥3 feedback** — `eval/USER_FEEDBACK.md` (gỡ điểm Product).
4. ⚠️ **Xác nhận LangSmith** có trace thật (chạy 1 lệnh "Chạy thật" → kiểm dashboard).
5. ⚠️ **Điền MSSV Nguyễn Đình Tiến Mạnh** (README + team).

## Verify cuối (trước khi bấm nộp)
- [ ] `pytest -q` + `ruff check src tests eval` → xanh.
- [ ] Mở live URL: `/health` ok · Demo nhanh chạy · 1 lần Chạy thật ok.
- [ ] README hiển thị đúng (badge, trạng thái, link live + report).
- [ ] `eval/results/report.md` có cả Bảng A + B; `.env` KHÔNG bị commit.
- [ ] Video + Pitch + tất cả link đã dán vào form nộp của BTC.

## Trung thực (giữ nguyên — đừng gỡ)
Showcase ghi rõ "thế giới mô phỏng · agent thật"; eval tách "agent Gemini thật (Bảng A)" vs "mock baseline (Bảng B)"; thừa nhận latency ~4.3s/bước + mẫu nhỏ. Đây là điểm tin cậy, không phải điểm yếu cần che.
