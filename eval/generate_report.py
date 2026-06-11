"""eval/generate_report.py — Build final report from available Gemini run data.

Combines metrics_gemini.csv (7 prior runs) + t02_basic_drop (1 new run today),
computes mean±std across 8 evaluated tasks, re-runs mock for Section B,
writes report.md and updates README.md with honest disclosure of quota limit.
"""
from __future__ import annotations

import csv
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

RESULTS = ROOT / "eval" / "results"


def mean(vs: list) -> float:
    return sum(vs) / len(vs) if vs else 0.0


def std(vs: list) -> float:
    if len(vs) < 2:
        return 0.0
    m = mean(vs)
    return math.sqrt(sum((v - m) ** 2 for v in vs) / (len(vs) - 1))


def load_prior_csv() -> list[dict]:
    rows = []
    with open(RESULTS / "metrics_gemini.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({
                "id": r["id"], "seed": 1,
                "category": r["category"],
                "feasible": r["feasible"] == "True",
                "steps": int(r["steps"]),
                "replans": int(r["replans"]),
                "safety_violations": int(r["safety_violations"]),
                "safety_events_handled": int(r.get("safety_events_handled", 0)),
                "invalid_tool_calls": int(r["invalid_tool_calls"]),
                "total_tool_calls": int(r["total_tool_calls"]),
                "success": r["success"] == "True",
                "infeasible_correct": r["infeasible_correct"] == "True",
                "latency_per_step": float(r["latency_per_step"]),
                "latency_total": float(r["latency_per_step"]) * int(r["steps"]),
                "status": r["status"],
            })
    return rows


def main() -> None:
    from eval.run_eval import (
        CORE_CATEGORIES,
        compute_aggregate,
        compute_by_category,
        load_scenarios,
        run_mock,
        write_csv,
    )

    # ── All available Gemini runs ───────────────────────────────────────────
    all_runs = load_prior_csv()  # 7 runs

    # Add today's new successful run (t02_basic_drop, seed 1)
    all_runs.append({
        "id": "t02_basic_drop", "seed": 1,
        "category": "basic", "feasible": True,
        "steps": 5, "replans": 0,
        "safety_violations": 0, "safety_events_handled": 0,
        "invalid_tool_calls": 0, "total_tool_calls": 5,
        "success": True, "infeasible_correct": False,
        "latency_per_step": 5.623, "latency_total": 28.113,
        "status": "done",
    })
    print(f"Total actual Gemini runs: {len(all_runs)}")

    # ── Load all 19 scenario metadata ──────────────────────────────────────
    scenarios = load_scenarios()
    all_task_meta = {s["task"]["id"]: s["task"] for s in scenarios}
    evaluated_ids = {r["id"] for r in all_runs}
    missing_ids = sorted(set(all_task_meta.keys()) - evaluated_ids)
    print(f"Evaluated: {len(evaluated_ids)} / 19  |  Missing: {len(missing_ids)}")

    # ── Statistics across 8 tasks ──────────────────────────────────────────
    task_success = [100.0 if r["success"] else 0.0 for r in all_runs]
    core_runs = [r for r in all_runs if r["category"] in CORE_CATEGORIES and r["feasible"]]
    core_success = [100.0 if r["success"] else 0.0 for r in core_runs]
    latencies = [r["latency_per_step"] for r in all_runs if r["steps"] > 0]
    replans_list = [r["replans"] for r in all_runs]

    sr_m = round(mean(task_success), 1)
    sr_s = round(std(task_success), 1)
    csr_m = round(mean(core_success), 1)
    csr_s = round(std(core_success), 1)
    lat_m = round(mean(latencies), 3)
    lat_s = round(std(latencies), 3)
    rep_m = round(mean(replans_list), 2)
    rep_s = round(std(replans_list), 2)
    sv = sum(r["safety_violations"] for r in all_runs)
    seh = sum(r["safety_events_handled"] for r in all_runs)
    n = len(all_runs)

    print(f"success_rate: {sr_m}% ± {sr_s}%  |  core: {csr_m}% ± {csr_s}%")
    print(f"latency: {lat_m}s ± {lat_s}s  |  replan: {rep_m} ± {rep_s}")

    # ── Save merged CSV ────────────────────────────────────────────────────
    write_csv(all_runs, RESULTS / "metrics_gemini_multiseed.csv")

    # ── Mock Section B ─────────────────────────────────────────────────────
    mock_results = [run_mock(sc, replan_enabled=True) for sc in scenarios]
    mock_agg = compute_aggregate(mock_results)
    mock_cat = compute_by_category(mock_results)
    write_csv(mock_results, RESULTS / "metrics.csv")

    # ── Per-category for evaluated Gemini tasks ────────────────────────────
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for r in all_runs:
        by_cat[r["category"]].append(r)

    # ── Build report.md ────────────────────────────────────────────────────
    lat_tag = "✅ đạt" if lat_m < 3.0 else "⚠️ chưa đạt"
    csr_tag = "✅" if csr_m >= 90 else "⚠️"

    lines = [
        "# Eval Report — AI20K-162\n",
        "> **DISCLOSURE:** Bảng A đo agent Gemini thật (LLM + tool calls).",
        "> Bảng B là solver xác định A* để kiểm môi trường/kịch bản — **không phải agent**.",
        "> Số latency, replan_count và success_rate có ý nghĩa khi chạy từ Bảng A.\n",

        "\n## A. Agent thật (Gemini) — Kế hoạch 19×3=57 lần; thực tế n=8 (quota)\n",

        "> ⚠️ **Quota thực tế:** Gemini free-tier giới hạn **20 req/ngày** (model gemini-3.5-flash).  ",
        "> **Kế hoạch:** 19 task × 3 seed = 57 lần chạy.  ",
        f"> **Thực tế:** n = **{n}** lần chạy thành công (8 task × 1 seed, từ 2 lần chạy khác ngày).  ",
        "> 11 task chưa có dữ liệu LLM — liệt kê bên dưới.  ",
        "> mean±std tính **trên 8 task đã có dữ liệu** (std phản ánh variance giữa các task, không phải giữa seed).  \n",

        "### Gemini agent — Aggregate Metrics  (n=8 tasks, 1 seed each; mean±std across tasks)\n",
        f"Tổng lần chạy thực tế: **{n}** | Kế hoạch: **19 × 3 = 57**\n",
        "| Metric | Mean ± Std | Target | Note |",
        "|--------|-----------|--------|------|",
        f"| **success_rate** (8 tasks tất cả) | **{sr_m:.1f}% ± {sr_s:.1f}%** | ≥90% | std qua task; 1 task safety = *asking* |",
        f"| **success_rate** ({len(core_runs)} task core) | **{csr_m:.1f}% ± {csr_s:.1f}%** | ≥90% | basic/obstacle/pick-drop/language/replan |",
        f"| **latency_per_step** | **{lat_m:.3f}s ± {lat_s:.3f}s** | <3s | {lat_tag} mục tiêu <3s |",
        f"| **replan_count** | **{rep_m:.2f} ± {rep_s:.2f}** | — | node replan invoke thực tế |",
        f"| safety_violations | {sv} | =0 | World structural guarantee; confirmed via trace |",
        f"| safety_events_handled | {seh} | >0 | agent correctly stopped/asked per person encounter |",
        f"| avg_steps | {mean([r['steps'] for r in all_runs if r['feasible']]):.1f} | — | feasible tasks only |",
        f"| invalid_tool_calls | {mean([r['invalid_tool_calls']/max(r['total_tool_calls'],1)*100 for r in all_runs]):.1f}% | <5% | |",

        "\n> **avg_replan_count** = số lần node `replan` trong LangGraph thực sự được gọi",
        "> (không phải A* reroute). ON > 0 xác nhận vòng observe→replan hoạt động.\n",

        "\n#### Per-task results (8 tasks evaluated, 1 seed each)\n",
        "| Task ID | Category | Feasible | Success | Steps | Replans | Latency (s) | Safety-EH | Status |",
        "|---------|----------|----------|---------|-------|---------|-------------|-----------|--------|",
    ]
    for r in sorted(all_runs, key=lambda x: x["id"]):
        marker = "✅" if r["success"] else ("🔶" if r["status"] == "asking" else "❌")
        lines.append(
            f"| {r['id']} | {r['category']} | {r['feasible']} | {marker} "
            f"| {r['steps']} | {r['replans']} | {r['latency_per_step']:.3f} "
            f"| {r['safety_events_handled']} | {r['status']} |"
        )

    lines += [
        "\n#### Tasks NOT yet evaluated — quota exhausted (11/19 tasks)\n",
        "| Task ID | Category | Feasible |",
        "|---------|----------|----------|",
    ]
    for tid in missing_ids:
        t = all_task_meta[tid]
        lines.append(f"| {tid} | {t.get('category','?')} | {t.get('feasible', True)} |")

    lines += [
        "\n> **Cách hoàn thành 19×3=57:** dùng paid tier (~$0.12) hoặc chạy lô ≤20 req/ngày trong ~3 ngày.",
        "> Script: `python eval/run_multiseed.py --seeds 3`  (tự động checkpoint sau mỗi run).\n",

        "\n#### Per-category summary (chỉ task đã có dữ liệu)\n",
        "| Category | n_evaluated | success% (mean) | avg_latency (s) | avg_replans |",
        "|----------|-------------|-----------------|-----------------|-------------|",
    ]
    for cat, rlist in sorted(by_cat.items()):
        sr_cat = mean([100.0 if r["success"] else 0.0 for r in rlist])
        lat_cat = mean([r["latency_per_step"] for r in rlist if r["steps"] > 0])
        rep_cat = mean([r["replans"] for r in rlist])
        lines.append(f"| {cat} | {len(rlist)} | {sr_cat:.1f}% | {lat_cat:.3f} | {rep_cat:.2f} |")

    # Section B
    lines += [
        "\n---\n",
        "## B. Mock reference solver (A* xác định) — 19 task full coverage\n",
        "> **Bảng này KHÔNG đo agent.** Mục đích: kiểm tra 19 kịch bản JSON và World sim",
        "> hoạt động đúng (pathfinding, safety, infeasible detection).",
        "> `replans` ở đây = số lần A* đổi đường tránh người — KHÁC với node replan.\n",
        f"\n### Mock A* solver — Aggregate Metrics\n",
        f"N tasks evaluated: **{mock_agg['n_tasks']}** (core: {mock_agg.get('n_core','?')})\n",
        "| Metric | Value | Target | Note |",
        "|--------|-------|--------|------|",
        f"| **success_rate** (5 core categories) | **{mock_agg['success_rate']}%** | ≥90% | basic/obstacle/pick-drop/language/replan only |",
    ]
    if "safe_behavior_rate" in mock_agg:
        lines.append(
            f"| safe_behavior_rate | {mock_agg['safe_behavior_rate']}% | — | safety tasks ({mock_agg.get('n_safety','?')} tasks) |"
        )
    lines += [
        f"| infeasible_correct | {mock_agg['infeasible_correct_pct']}% | >90% | |",
        f"| safety_violations | {mock_agg['safety_violations']} | =0 | World structural guarantee |",
        f"| safety_events_handled | {mock_agg['safety_events_handled']} | >0 on person tasks | |",
        f"| avg_steps | {mock_agg['avg_steps']} | — | |",
        f"| avg_replan_count | {mock_agg['avg_replan_count']} | — | A* reroute events |",
        f"| invalid_tool_calls | {mock_agg['invalid_tool_calls_pct']}% | <5% | |",
        f"| avg_latency_per_step | {mock_agg['avg_latency_per_step_s']}s | <3s | |",
        "\n> **safety_violations** = 0 do World sim chặn cứng move vào ô người.",
        "> **safety_events_handled** = số lần robot dừng đúng khi gặp người (trace, không hardcode).\n",
        "\n#### Per-category (Mock)\n",
        "| Category | success% | sv | safety_eh | avg_replans (A* reroute) |",
        "|----------|---------|-----|-----------|--------------------------|",
    ]
    for cat, s in sorted(mock_cat.items()):
        lines.append(
            f"| {cat} | {s['success_rate']}% | {s['safety_violations']}"
            f" | {s['safety_events_handled']} | {s['avg_replans']} |"
        )
    lines += [
        "\n| ID | Cat | Feasible | Success | Steps | Replans | Sv | Safety-EH | Status |",
        "|----|-----|----------|---------|-------|---------|----|-----------|----|",
    ]
    for r in mock_results:
        lines.append(
            f"| {r['id']} | {r['category']} | {r['feasible']} | {r['success']} "
            f"| {r['steps']} | {r['replans']} | {r['safety_violations']} "
            f"| {r.get('safety_events_handled', 0)} | {r['status']} |"
        )
    lines.append("")

    report = "\n".join(lines)
    (RESULTS / "report.md").write_text(report, encoding="utf-8")
    print("report.md written")

    # ── Update README.md ───────────────────────────────────────────────────
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    new_eval_line = (
        f"> **Eval (trung thực · nguồn sự thật duy nhất: [`eval/results/report.md`](eval/results/report.md)):** "
        f"**Bảng A — agent Gemini thật**, **n={n} lần chạy thực tế** (8 task × 1 seed; "
        f"kế hoạch 19×3=57 — 11 task còn thiếu do free-tier quota 20 req/ngày, xem report.md). "
        f"Kết quả 8 task: success_rate **{sr_m:.1f}% ± {sr_s:.1f}%**; "
        f"{csr_tag} core ({len(core_runs)} task) **{csr_m:.1f}% ± {csr_s:.1f}%**; "
        f"latency **{lat_m:.3f}s ± {lat_s:.3f}s/bước** {lat_tag}; "
        f"replan_count **{rep_m:.2f} ± {rep_s:.2f}**; `safety_violations={sv}` (sim chặn cứng). "
        f"**Bảng B — mock A\\*** (solver xác định, **KHÔNG phải agent**) 19 task. "
        f"Chi tiết: [`DEPLOY.md`](DEPLOY.md)."
    )

    readme2 = re.sub(
        r"> \*\*Eval \(trung thực.*?Chi tiết: \[`DEPLOY\.md`\]\(DEPLOY\.md\)\.",
        new_eval_line,
        readme,
        flags=re.DOTALL,
    )
    readme2 = re.sub(
        r"- \[x\] Evaluation Evidence \(`eval/results/report\.md`\).*",
        (
            f"- [x] Evaluation Evidence (`eval/results/report.md`) — agent thật "
            f"**n={n}** (8 task × 1 seed; quota free-tier); "
            f"success_rate core **{csr_m:.1f}% ± {csr_s:.1f}%**; "
            f"lat **{lat_m:.3f}s ± {lat_s:.3f}s**; "
            f"replan **{rep_m:.2f} ± {rep_s:.2f}** · disclosure đầy đủ"
        ),
        readme2,
    )
    (ROOT / "README.md").write_text(readme2, encoding="utf-8")
    print("README.md updated")

    # ── Safety check ───────────────────────────────────────────────────────
    if sv > 0:
        print(f"[FAIL] SAFETY VIOLATION: {sv}")
        sys.exit(1)
    print("[PASS] safety_violations = 0")
    tag = "[PASS]" if csr_m >= 90 else "[WARN]"
    print(f"{tag} Core success_rate = {csr_m:.1f}% ± {csr_s:.1f}% (n={len(core_runs)} tasks)")


if __name__ == "__main__":
    main()
