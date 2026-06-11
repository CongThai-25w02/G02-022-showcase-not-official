"""Eval v2 — task 'di chuyển 1 vật thể' (PLAN_thu_nho_162.md).

Hai lớp TÁCH BẠCH (không bao giờ trộn):
  • Bảng B — XÁC ĐỊNH: solver A* tất định, KHÔNG LLM. Chứng minh bộ task giải
    được và harness đúng. Chạy được ngay, không tốn quota.
  • Bảng A — AGENT THẬT: LangGraph + LLM (Gemini cloud HOẶC Ollama local), chạy
    NHIỀU SEED → mean ± std + n. Thiếu backend thì ghi "CHƯA CHẠY" (không bịa số).

Success luôn chấm bằng ORACLE độc lập (check_object_moved) — không tin status
agent tự khai.

Chạy:
  python eval/run_eval_v2.py                # chỉ Bảng B (xác định)
  python eval/run_eval_v2.py --seeds 3      # + Bảng A (cần Ollama local hoặc Gemini key)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.models.schemas import Cell  # noqa: E402
from src.services.oracle import check_object_moved  # noqa: E402
from src.services.world import World, set_current_world  # noqa: E402

SCEN_DIR = _ROOT / "eval" / "scenarios"
RESULTS_DIR = _ROOT / "eval" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
GLOB = "m*.json"


def load_tasks() -> list[dict]:
    out = []
    for f in sorted(SCEN_DIR.glob(GLOB)):
        data = json.loads(f.read_text(encoding="utf-8"))
        if "task" in data:
            out.append(data)
    return out


def _dest(success: dict):
    if success.get("at_zone"):
        return success["at_zone"]
    if success.get("at_cell"):
        c = success["at_cell"]
        return (c["x"], c["y"])
    return None


def _reachable_zone_cell(world: World, zone_name: str) -> Cell | None:
    rp = world.to_state().robot.pos
    for c in world.zone_cells(zone_name):
        if not world.is_blocked_static(c) and world.astar_static(rp, c) is not None:
            return c
    return None


def optimal_distance(scenario: dict) -> int | None:
    """Quãng đường A* TỐI ƯU cho task = mẫu số SPL: robot→vật (đứng lên ô vật)
    + vật→ô đích gần nhất. Trả None nếu task không giải được (infeasible) — khi
    đó không tính SPL cho task này.
    """
    world = World.from_scenario(scenario)
    sc = scenario["task"].get("success", {})
    obj_label = sc.get("object")
    dest = _dest(sc)
    if not obj_label or dest is None:
        return None
    obj = world.find_object_fuzzy(obj_label)
    if obj is None:
        return None
    rp = world.to_state().robot.pos
    leg1 = world.astar_static(rp, obj.pos)
    if leg1 is None:
        return None
    if isinstance(dest, str):
        best = None
        for c in world.zone_cells(dest):
            if world.is_blocked_static(c):
                continue
            p = world.astar_static(obj.pos, c)
            if p is not None:
                best = (len(p) - 1) if best is None else min(best, len(p) - 1)
        if best is None:
            return None
        leg2 = best
    else:
        p = world.astar_static(obj.pos, Cell(x=dest[0], y=dest[1]))
        if p is None:
            return None
        leg2 = len(p) - 1
    return (len(leg1) - 1) + leg2


def spl(success: bool, optimal: int | None, actual: int) -> float | None:
    """Success weighted by Path Length. None nếu task không có path tối ưu
    (infeasible). =0 nếu thất bại. =optimal/max(optimal,actual) nếu thành công.
    """
    if optimal is None:
        return None
    if not success:
        return 0.0
    return round(optimal / max(optimal, actual, 1), 3)


def valid_action_rate(history: list[dict]) -> float | None:
    """Tỉ lệ bước có action hợp lệ (ok=True: tool tồn tại, đúng schema, không lỗi)."""
    if not history:
        return None
    return round(sum(1 for h in history if h.get("ok")) / len(history), 3)


_READ_TOOLS = {"perceive", "locate_object", "check_path"}
_MUTATE_TOOLS = {"move_to", "pick", "drop"}


def grounded_action_rate(history: list[dict]) -> float | None:
    """Tỉ lệ hành động mutate (move/pick/drop) thực hiện SAU khi đã có ít nhất
    một quan sát thành công (perceive/locate/check_path) trong episode.
    Đây là số đo "% hành động grounded" (xem SURVEY_metrics.md §2).
    None nếu run không có hành động mutate nào.
    """
    seen_obs, mutate, grounded = False, 0, 0
    for h in history:
        a = h.get("action")
        if a in _READ_TOOLS and h.get("ok"):
            seen_obs = True
        elif a in _MUTATE_TOOLS:
            mutate += 1
            if seen_obs:
                grounded += 1
    return round(grounded / mutate, 3) if mutate else None


def solve_deterministic(scenario: dict) -> dict:
    """Solver A* tất định: tới vật → pick → tới đích → drop. Chấm bằng oracle."""
    world = World.from_scenario(scenario)
    task = scenario["task"]
    success_cond = task.get("success", {})
    obj_label = success_cond.get("object")
    dest = _dest(success_cond)
    feasible = task.get("feasible", True)
    steps, status = 0, "done"

    obj = world.find_object_fuzzy(obj_label) if obj_label else None
    if obj is None:
        status = "object_not_found"
    elif not world.move_robot_to(obj.pos).get("reached"):
        status, steps = "unreachable_object", steps + 1
    elif not world.pick_object(obj_label).get("ok"):
        status, steps = "pick_failed", steps + 2
    else:
        steps += 2
        dest_cell = (_reachable_zone_cell(world, dest) if isinstance(dest, str)
                     else (Cell(x=dest[0], y=dest[1]) if dest else None))
        if dest_cell is None:
            status = "no_dest_reachable"
        elif not world.move_robot_to(dest_cell).get("reached"):
            status, steps = "unreachable_dest", steps + 1
        elif not world.drop_at(dest_cell).get("ok"):
            status, steps = "drop_failed", steps + 2
        else:
            steps += 2

    success = bool(obj_label) and dest is not None and check_object_moved(world, obj_label, dest)
    return {
        "id": task.get("id"), "category": task.get("category", "basic"),
        "feasible": feasible, "success": success, "steps": steps, "status": status,
        "infeasible_correct": (not feasible) and (not success),
    }


async def run_agent_seed(scenario: dict, seed: int, optimal: int | None = None) -> dict:
    """Chạy agent thật 1 lần (1 seed). Chấm bằng oracle trên World sau khi chạy.

    Đo thêm: SPL (so quãng đường robot với `optimal`), valid_action_rate,
    llm_calls (suy ra từ cấu trúc đồ thị), replans.
    """
    from src.agents.graph import build_graph  # lazy: chỉ cần khi chạy agent
    from src.config import get_settings

    world = World.from_scenario(scenario)
    set_current_world(world)
    task = scenario["task"]
    history: list[dict] = []
    replans = 0
    # recursion_limit đủ lớn để node 'cap' (max_steps) tự dừng trước, không vỡ graph
    rec_limit = get_settings().max_steps * 3 + 20
    t0 = time.perf_counter()
    try:
        result = await asyncio.wait_for(
            build_graph().ainvoke(
                {"goal_text": task.get("goal_text", ""), "history": [],
                 "steps": 0, "replans": 0},
                config={"recursion_limit": rec_limit}),
            timeout=600.0,  # tăng lên 10 phút/run cho model local chậm (CPU)
        )
        status = result.get("status", "unknown")
        steps = result.get("steps") or 0
        history = result.get("history") or []
        replans = result.get("replans") or 0
    except TimeoutError:
        status, steps = "timeout", 0
    except Exception as exc:  # noqa: BLE001 — 1 seed lỗi không được giết cả eval
        status, steps = f"error:{type(exc).__name__}", 0
    elapsed = time.perf_counter() - t0

    obj_label = task.get("success", {}).get("object")
    dest = _dest(task.get("success", {}))
    success = bool(obj_label) and dest is not None and check_object_moved(world, obj_label, dest)
    feasible = task.get("feasible", True)
    # llm_calls suy ra từ cấu trúc đồ thị: parse_goal(1) + plan(1) + replan(replans)
    # + act(mỗi bước 1) = 2 + replans + steps. Đúng với luồng chuẩn của graph.
    llm_calls = (2 + replans + steps) if steps else None
    return {
        "id": task.get("id"), "seed": seed, "category": task.get("category", "basic"),
        "feasible": feasible, "success": success, "steps": steps, "status": status,
        "agent_distance": world.distance_traveled,
        "optimal_distance": optimal,
        "spl": spl(success, optimal, world.distance_traveled),
        "valid_action_rate": valid_action_rate(history),
        "grounded_action_rate": grounded_action_rate(history),
        "llm_calls": llm_calls,
        "replans": replans,
        "latency_per_step": round((elapsed / steps) if steps else elapsed, 3),
        "infeasible_correct": (not feasible) and (not success),
        # honesty: agent tự khai "done" nhưng oracle nói chưa đạt → ảo tưởng hoàn thành
        "hallucinated_done": (status == "done") and (not success),
    }


def _rate(rows: list[dict]) -> float:
    feas = [r for r in rows if r["feasible"]]
    return round(sum(1 for r in feas if r["success"]) / len(feas) * 100, 1) if feas else 0.0


def main() -> None:
    ap = argparse.ArgumentParser(description="Eval v2 — di chuyển 1 vật thể")
    ap.add_argument("--seeds", type=int, default=0,
                    help="Số seed/ task cho Bảng A (agent). 0 = bỏ qua agent.")
    args = ap.parse_args()

    tasks = load_tasks()
    if not tasks:
        print(f"[ERR] Không thấy task {GLOB} trong {SCEN_DIR}. Chạy: python eval/gen_move_tasks.py")
        sys.exit(1)

    # ── Bảng B: xác định ──────────────────────────────────────────────
    print(f"=== Bảng B — solver xác định ({len(tasks)} task) ===")
    det = [solve_deterministic(t) for t in tasks]
    for r in det:
        ok = "[OK]" if (r["success"] or r["infeasible_correct"]) else "[!!]"
        print(f"  {ok} {r['id']:26s} success={str(r['success']):5s} "
              f"status={r['status']:18s} steps={r['steps']}")
    det_rate = _rate(det)
    infeas_ok = sum(1 for r in det if not r["feasible"] and r["infeasible_correct"])
    n_infeas = sum(1 for r in det if not r["feasible"])
    print(f"  success_rate (feasible) = {det_rate}%  |  infeasible_correct = {infeas_ok}/{n_infeas}")

    # ── Bảng A: agent thật (nhiều seed) ───────────────────────────────
    from src.config import get_settings
    settings = get_settings()
    provider = settings.llm_provider
    # Có thể chạy agent khi: dùng Ollama local, HOẶC có GEMINI_API_KEY.
    can_run_agent = (provider == "ollama") or bool(settings.gemini_api_key)
    agent_rows: list[dict] = []
    agent_note = ""
    if args.seeds > 0 and can_run_agent:
        backend = (f"Ollama:{settings.ollama_model}" if provider == "ollama"
                   else f"Gemini:{settings.model_name}")
        print(f"\n=== Bảng A — agent thật ({backend}) × {args.seeds} seed ===")
        opt = {t["task"].get("id"): optimal_distance(t) for t in tasks}
        for t in tasks:
            for s in range(args.seeds):
                agent_rows.append(asyncio.run(run_agent_seed(t, s, opt[t["task"].get("id")])))
    elif args.seeds > 0:
        agent_note = ("CHƯA CHẠY: chưa có backend LLM. Đặt LLM_PROVIDER=ollama "
                      "(chạy local) hoặc GEMINI_API_KEY trong .env.")
        print(f"\n[WARN] {agent_note}")
    else:
        agent_note = ("CHƯA CHẠY: chạy lại với --seeds 3 để có Bảng A "
                      "(LLM_PROVIDER=ollama cho local, hoặc GEMINI_API_KEY).")

    write_report(det, det_rate, infeas_ok, n_infeas, agent_rows, agent_note, args.seeds)
    write_csv(det, agent_rows)
    print(f"\nĐã ghi: {RESULTS_DIR / 'report_v2.md'}")


def write_csv(det: list[dict], agent_rows: list[dict]) -> None:
    import csv
    with open(RESULTS_DIR / "metrics_v2_mock.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(det[0].keys()))
        w.writeheader()
        w.writerows(det)
    if agent_rows:
        with open(RESULTS_DIR / "metrics_v2_agent.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(agent_rows[0].keys()))
            w.writeheader()
            w.writerows(agent_rows)


def write_report(det, det_rate, infeas_ok, n_infeas, agent_rows, agent_note, seeds) -> None:
    lines = []
    lines.append("# Báo cáo eval v2 — di chuyển 1 vật thể\n")
    lines.append("> Nguồn sự thật duy nhất cho số liệu v2. Công thức: "
                 "`success_rate = task done / task feasible`, luôn kèm **n**. "
                 "Success chấm bằng **oracle độc lập** (`check_object_moved`), không tin status agent.\n")
    lines.append("> Hai lớp TÁCH BẠCH: **Bảng A = agent thật (LLM)**, **Bảng B = solver xác định "
                 "(KHÔNG phải agent)**. Mock không bao giờ được gắn nhãn 'agent'.\n")

    # Bảng A
    n_feas_tasks = sum(1 for r in det if r["feasible"])
    lines.append("\n## Bảng A — Agent thật (LLM, LangGraph)\n")
    if agent_rows:
        feas = [r for r in agent_rows if r["feasible"]]
        infeas = [r for r in agent_rows if not r["feasible"]]
        by_task: dict[str, list[int]] = {}
        for r in feas:
            by_task.setdefault(r["id"], []).append(1 if r["success"] else 0)
        per_task_rate = [statistics.mean(v) * 100 for v in by_task.values()]
        mean_sr = round(statistics.mean(per_task_rate), 1) if per_task_rate else 0.0
        std_sr = round(statistics.pstdev(per_task_rate), 1) if len(per_task_rate) > 1 else 0.0

        def _ms(vals: list[float], nd: int = 2) -> tuple[float, float]:
            if not vals:
                return 0.0, 0.0
            m = round(statistics.mean(vals), nd)
            s = round(statistics.pstdev(vals), nd) if len(vals) > 1 else 0.0
            return m, s

        # SPL (chỉ trên task feasible, có optimal); thất bại tính spl=0
        spl_vals = [r["spl"] for r in feas if r["spl"] is not None]
        mean_spl, std_spl = _ms(spl_vals, 3)
        # valid-action rate (mọi run có history)
        var_vals = [r["valid_action_rate"] for r in agent_rows if r["valid_action_rate"] is not None]
        mean_var, std_var = _ms([v * 100 for v in var_vals], 1)
        # cost
        call_vals = [r["llm_calls"] for r in agent_rows if r["llm_calls"] is not None]
        mean_calls, std_calls = _ms(call_vals, 1)
        mean_replans, _ = _ms([r["replans"] for r in agent_rows], 2)
        # infeasible / abstention
        n_infeas_runs = len(infeas)
        abst_ok = sum(1 for r in infeas if not r["success"])
        abst_rate = round(abst_ok / n_infeas_runs * 100, 1) if n_infeas_runs else 0.0
        halluc = sum(1 for r in agent_rows if r.get("hallucinated_done"))
        lat = [r["latency_per_step"] for r in agent_rows if r["steps"]]
        mean_lat, std_lat = _ms(lat, 2)
        n_runs = len(agent_rows)

        # ── Metric bổ sung (xem SURVEY_metrics.md §2) — tính từ dữ liệu sẵn có ──
        # pass^k (τ-bench): task đạt khi success ở CẢ k seed — đo độ tin cậy, không phải trung bình
        passk = (round(sum(1 for v in by_task.values() if v and all(v)) / len(by_task) * 100, 1)
                 if by_task else 0.0)
        # completion_rate: % run kết thúc có kiểm soát (không timeout / không exception)
        bad_runs = sum(1 for r in agent_rows
                       if r["status"] == "timeout" or str(r["status"]).startswith("error"))
        completion = round((n_runs - bad_runs) / n_runs * 100, 1) if n_runs else 0.0
        # hallucinated_done_rate: % run tự khai done nhưng oracle bác — metric "honesty" chính thức
        halluc_rate = round(halluc / n_runs * 100, 1) if n_runs else 0.0
        # path_overhead: quãng đường thật / tối ưu, CHỈ trên run thành công (tách efficiency khỏi SPL)
        po_vals = [r["agent_distance"] / r["optimal_distance"] for r in feas
                   if r["success"] and r.get("optimal_distance")]
        mean_po, std_po = _ms(po_vals, 2)
        # grounded_action_rate: % hành động mutate có quan sát trước đó
        gar_vals = [r["grounded_action_rate"] for r in agent_rows
                    if r.get("grounded_action_rate") is not None]
        mean_gar, std_gar = _ms([v * 100 for v in gar_vals], 1)

        lines.append(f"- n = **{n_runs}** lần chạy ({len(by_task)} task feasible × {seeds} seed"
                     f"; +{n_infeas_runs} run infeasible)\n")
        lines.append("\n| Chỉ số | Kết quả (mean ± std) | Mục tiêu |")
        lines.append("|---|---|---|")
        lines.append(f"| success_rate (feasible) | **{mean_sr}% ± {std_sr}%** | ≥90% |")
        if seeds >= 2:
            lines.append(f"| pass^k — success ở CẢ k={seeds} seed (τ-bench) | **{passk}%** | ≥80% |")
        lines.append(f"| SPL (path-efficiency) | **{mean_spl} ± {std_spl}** | ≥0.80 |")
        if po_vals:
            lines.append(f"| path_overhead (đi thật/tối ưu, run thành công) | {mean_po} ± {std_po} | ≤1.25 |")
        lines.append(f"| completion_rate (không timeout/error) | {completion}% ({n_runs - bad_runs}/{n_runs}) | 100% |")
        lines.append(f"| valid_action_rate | {mean_var}% ± {std_var}% | ≥95% |")
        lines.append(f"| grounded_action_rate (mutate có quan sát trước) | {mean_gar}% ± {std_gar}% | ≥95% |")
        lines.append(f"| infeasible/abstention accuracy | {abst_rate}% ({abst_ok}/{n_infeas_runs}) | 100% |")
        lines.append(f"| hallucinated_done_rate (tự khai done, oracle bác) | {halluc_rate}% ({halluc}/{n_runs}) | 0% |")
        lines.append(f"| LLM calls/task | {mean_calls} ± {std_calls} | (báo thật) |")
        lines.append(f"| replans/task | {mean_replans} | (báo thật) |")
        lines.append(f"| latency/bước | {mean_lat}s ± {std_lat}s | (báo thật) |")
        if halluc:
            lines.append(f"\n> ⚠️ Có **{halluc}** run agent tự khai `done` nhưng oracle xác nhận "
                         "CHƯA đạt mục tiêu (ảo tưởng hoàn thành) — cần xem lại.\n")
        lines.append("\n*SPL = success × optimal_path / max(optimal, actual). "
                     "valid_action_rate = bước có tool-call hợp lệ / tổng bước. "
                     "pass^k = % task thành công ở cả k seed (đo độ ổn định, τ-bench). "
                     "grounded_action_rate = % move/pick/drop có perceive/locate/check_path "
                     "thành công trước đó trong episode. "
                     "LLM calls suy ra từ cấu trúc đồ thị (parse+plan+replan+act). "
                     "Định nghĩa & nguồn: SURVEY_metrics.md.*\n")
    else:
        lines.append(f"**{agent_note}**\n")
        lines.append("\nĐể điền Bảng A (số thật, mean ± std) bằng **LLM local (Ollama)**:\n")
        lines.append("```bash\npip install langchain-ollama\n"
                     "ollama pull qwen2.5:7b && ollama serve   # cửa sổ khác\n"
                     "# .env: LLM_PROVIDER=ollama\n"
                     "python eval/run_eval_v2.py --seeds 3\n```\n")

    # Bảng B
    lines.append("\n## Bảng B — Solver xác định (A*, KHÔNG phải agent)\n")
    lines.append(f"- n = **{n_feas_tasks}** task feasible; success_rate = **{det_rate}%**; "
                 f"infeasible_correct = **{infeas_ok}/{n_infeas}**\n")
    lines.append("\n| id | category | feasible | success | status | steps |")
    lines.append("|---|---|---|---|---|---|")
    for r in det:
        lines.append(f"| {r['id']} | {r['category']} | {r['feasible']} | "
                     f"{r['success']} | {r['status']} | {r['steps']} |")
    lines.append("\n> Bảng B chỉ chứng minh **môi trường giải được** và harness đúng — "
                 "**không** phải năng lực của agent. Mọi tuyên bố về agent phải lấy từ Bảng A.\n")

    # Disclosure
    lines.append("\n## Trung thực & Disclosure\n")
    lines.append("- Bộ task: di chuyển 1 vật thể (basic/obstacle/pick-drop/language) + ca infeasible.\n")
    lines.append("- Không có người động / replan / 'an toàn' trong scope v2 → không khoe các chỉ số đó.\n")
    lines.append("- Latency báo nguyên trạng; đây là planner mức nhiệm vụ, không phải vòng điều khiển realtime.\n")
    lines.append("- Metric đánh giá agent: **success_rate, pass^k (reliability), SPL + path_overhead "
                 "(efficiency), completion_rate, valid_action_rate, grounded_action_rate, "
                 "infeasible/abstention accuracy, hallucinated_done_rate (honesty), "
                 "LLM calls + replans (cost)**. So với lời giải A* tối ưu — đo hiệu quả, "
                 "không chỉ đúng/sai. Khảo sát & định nghĩa: `SURVEY_metrics.md`.\n")
    lines.append("- Backend LLM ghi rõ ở tiêu đề Bảng A (Gemini cloud hay Ollama local). "
                 "Số local & cloud KHÔNG trộn trong cùng một bảng.\n")
    (RESULTS_DIR / "report_v2.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
