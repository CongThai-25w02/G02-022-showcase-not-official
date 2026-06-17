/* =====================================================================
   ScenariosUI — shared catalog loader for 2D + 3D frontends
   Fetches GET /api/v1/scenarios and populates dropdown + eval chips.
   ===================================================================== */
(function (global) {
  "use strict";

  const GROUP_ORDER = ["demo", "eval_v2", "eval_v1"];

  let catalog = [];
  let evalQuick = [];
  let byId = {};

  function indexCatalog() {
    byId = Object.fromEntries(catalog.map((s) => [s.id, s]));
  }

  function goalFromState(state) {
    if (state && state.task && state.task.goal_text) return state.task.goal_text;
    const id = state && state._scenarioId;
    if (id && byId[id]) return byId[id].goal_text || "";
    return "";
  }

  function populateSelect(selectEl, selectedId) {
    if (!selectEl) return;
    selectEl.innerHTML = "";

    const grouped = {};
    for (const s of catalog) {
      if (!grouped[s.group]) grouped[s.group] = { label: s.group_label, items: [] };
      grouped[s.group].items.push(s);
    }

    for (const gid of GROUP_ORDER) {
      const g = grouped[gid];
      if (!g || !g.items.length) continue;
      const og = document.createElement("optgroup");
      og.label = g.label;
      for (const s of g.items) {
        const opt = document.createElement("option");
        opt.value = s.id;
        opt.textContent = s.label;
        if (s.id === selectedId) opt.selected = true;
        og.appendChild(opt);
      }
      selectEl.appendChild(og);
    }
  }

  function buildEvalChips(containerEl, onSelect) {
    if (!containerEl) return;
    containerEl.innerHTML = "";
    for (const chip of evalQuick) {
      const meta = byId[chip.id] || chip;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chip chip-eval";
      btn.dataset.scenario = chip.id;
      btn.innerHTML =
        `<span class="chip-icon">${chip.icon || "🧪"}</span>` +
        `<span class="chip-text">${chip.text || meta.label || chip.id}</span>` +
        `<span class="chip-cap">${chip.cap || meta.category || ""}</span>`;
      btn.addEventListener("click", () => {
        if (typeof onSelect === "function") onSelect(chip.id, meta);
      });
      containerEl.appendChild(btn);
    }
  }

  async function fetchCatalog() {
    try {
      const resp = await fetch("/api/v1/scenarios");
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      catalog = data.scenarios || [];
      evalQuick = data.eval_quick || [];
    } catch (_e) {
      catalog = FALLBACK_CATALOG;
      evalQuick = FALLBACK_EVAL_QUICK;
    }
    indexCatalog();
    return catalog;
  }

  function getGoalText(scenarioId, state) {
    const fromState = goalFromState(Object.assign({}, state || {}, { _scenarioId: scenarioId }));
    if (fromState) return fromState;
    return (byId[scenarioId] && byId[scenarioId].goal_text) || "";
  }

  function applyGoal(goalInput, scenarioId, state) {
    if (!goalInput) return;
    const goal = getGoalText(scenarioId, state);
    if (goal) goalInput.value = goal;
  }

  // Minimal fallback when backend is offline (dropdown still usable for labels)
  const FALLBACK_CATALOG = [
    { id: "warehouse_blocked", label: "Kho có người chặn lối (hero)", group: "demo", group_label: "Demo kho (live)", goal_text: "Đưa pallet A tới chuyền 3, tránh người" },
    { id: "warehouse_basic", label: "Kho cơ bản (không người)", group: "demo", group_label: "Demo kho (live)", goal_text: "Đưa pallet A tới chuyền 3" },
    { id: "warehouse_dynamic", label: "Kho động (người di chuyển)", group: "demo", group_label: "Demo kho (live)", goal_text: "Đưa pallet A tới chuyền 3" },
    { id: "m01_basic_a", label: "m01 — Di chuyển pallet A → chuyền 3", group: "eval_v2", group_label: "Eval v2 — metrics (m01–m11)", goal_text: "Đưa pallet A từ khu A sang chuyền 3" },
    { id: "m02_basic_b", label: "m02 — Đưa thùng B → kho B", group: "eval_v2", group_label: "Eval v2 — metrics (m01–m11)", goal_text: "Đưa thùng B tới kho B" },
    { id: "m03_basic_c", label: "m03 — Mang kiện C → chuyền 3", group: "eval_v2", group_label: "Eval v2 — metrics (m01–m11)", goal_text: "Mang kiện C tới chuyền 3" },
    { id: "m04_obstacle_wall", label: "m04 — Vượt tường cản tĩnh", group: "eval_v2", group_label: "Eval v2 — metrics (m01–m11)", goal_text: "Đưa pallet A qua tường tới chuyền 3" },
    { id: "m05_obstacle_detour", label: "m05 — Đi vòng chướng ngại", group: "eval_v2", group_label: "Eval v2 — metrics (m01–m11)", goal_text: "Đưa thùng B vòng chướng ngại tới kho B" },
    { id: "m06_obstacle_narrow", label: "m06 — Hành lang hẹp", group: "eval_v2", group_label: "Eval v2 — metrics (m01–m11)", goal_text: "Đưa kiện C qua lối hẹp tới chuyền 3" },
    { id: "m07_pickdrop_far", label: "m07 — Gắp thả khoảng cách xa", group: "eval_v2", group_label: "Eval v2 — metrics (m01–m11)", goal_text: "Nhặt pallet A và đưa tới chuyền 3" },
    { id: "m08_pickdrop_cross", label: "m08 — Gắp thả chéo kho", group: "eval_v2", group_label: "Eval v2 — metrics (m01–m11)", goal_text: "Nhặt kiện C rồi để ở kho B" },
    { id: "m09_language_case", label: "m09 — Kiểm tra chữ hoa/thường", group: "eval_v2", group_label: "Eval v2 — metrics (m01–m11)", goal_text: "ĐƯA Pallet a TỚI Chuyền 3" },
    { id: "m10_infeasible_missing", label: "m10 — Pallet không tồn tại", group: "eval_v2", group_label: "Eval v2 — metrics (m01–m11)", goal_text: "Đưa pallet Z tới chuyền 3" },
    { id: "m11_infeasible_enclosed", label: "m11 — Hàng bị bịt kín", group: "eval_v2", group_label: "Eval v2 — metrics (m01–m11)", goal_text: "Đưa hộp kẹt tới chuyền 3" },
    { id: "t01_basic_move", label: "t01 — Di chuyển cơ bản", group: "eval_v1", group_label: "Eval v1 — bộ task (t01–t19)", goal_text: "Đưa pallet A từ khu A sang chuyền 3" },
    { id: "t02_basic_drop", label: "t02 — Đưa thùng B → khu A", group: "eval_v1", group_label: "Eval v1 — bộ task (t01–t19)", goal_text: "Đưa thùng B sang khu A" },
    { id: "t03_obstacle_route", label: "t03 — Đi vòng qua tường", group: "eval_v1", group_label: "Eval v1 — bộ task (t01–t19)", goal_text: "Đưa pallet A sang chuyền 3 (vòng qua tường)" },
    { id: "t04_obstacle_narrow", label: "t04 — Hành lang hẹp một lối", group: "eval_v1", group_label: "Eval v1 — bộ task (t01–t19)", goal_text: "Đưa pallet A sang chuyền 3 qua hành lang hẹp" },
    { id: "t05_pick_move_first", label: "t05 — Phải đến gần mới gắp", group: "eval_v1", group_label: "Eval v1 — bộ task (t01–t19)", goal_text: "Nhặt pallet A và đưa đến chuyền 3" },
    { id: "t06_multi_goal", label: "t06 — Đa mục tiêu (A rồi B)", group: "eval_v1", group_label: "Eval v1 — bộ task (t01–t19)", goal_text: "Đưa pallet A đến chuyền 3" },
    { id: "t07_language_case", label: "t07 — Chữ hoa/thường pallet", group: "eval_v1", group_label: "Eval v1 — bộ task (t01–t19)", goal_text: "đưa Pallet a tới chuyền 3" },
    { id: "t08_language_constraint", label: "t08 — Ràng buộc tránh người", group: "eval_v1", group_label: "Eval v1 — bộ task (t01–t19)", goal_text: "Đưa pallet A đến chuyền 3, tránh người" },
    { id: "t09_replan_person_blocks", label: "t09 — Người chặn giữa chừng", group: "eval_v1", group_label: "Eval v1 — bộ task (t01–t19)", goal_text: "Đưa pallet A sang chuyền 3" },
    { id: "t10_replan_detour", label: "t10 — Replan đường vòng dài", group: "eval_v1", group_label: "Eval v1 — bộ task (t01–t19)", goal_text: "Đưa pallet A sang chuyền 3" },
    { id: "t11_replan_wait", label: "t11 — Chờ người rồi đi", group: "eval_v1", group_label: "Eval v1 — bộ task (t01–t19)", goal_text: "Đưa pallet A sang chuyền 3, chờ nếu bị chặn" },
    { id: "t12_safety_adjacent", label: "t12 — Người sát robot → dừng", group: "eval_v1", group_label: "Eval v1 — bộ task (t01–t19)", goal_text: "Đưa pallet A sang chuyền 3" },
    { id: "t13_safety_at_dest", label: "t13 — Người chắn ngay đích", group: "eval_v1", group_label: "Eval v1 — bộ task (t01–t19)", goal_text: "Đưa pallet A sang chuyền 3" },
    { id: "t14_safety_two_people", label: "t14 — Hai người cắt đường", group: "eval_v1", group_label: "Eval v1 — bộ task (t01–t19)", goal_text: "Đưa pallet A sang chuyền 3" },
    { id: "t15_infeasible_enclosed", label: "t15 — Đích bị bao kín", group: "eval_v1", group_label: "Eval v1 — bộ task (t01–t19)", goal_text: "Đưa pallet A sang chuyền 3" },
    { id: "t16_infeasible_missing", label: "t16 — Vật không tồn tại", group: "eval_v1", group_label: "Eval v1 — bộ task (t01–t19)", goal_text: "Đưa thùng Z sang chuyền 3" },
    { id: "t17_robustness_vague", label: "t17 — Mệnh lệnh mơ hồ", group: "eval_v1", group_label: "Eval v1 — bộ task (t01–t19)", goal_text: "đưa hàng đi" },
    { id: "t18_robustness_large", label: "t18 — Bản đồ lớn nhiều nhiễu", group: "eval_v1", group_label: "Eval v1 — bộ task (t01–t19)", goal_text: "Đưa pallet A sang chuyền 3" },
    { id: "t19_replan_midpath_block", label: "t19 — Replan giữa đường", group: "eval_v1", group_label: "Eval v1 — bộ task (t01–t19)", goal_text: "Đưa pallet A sang chuyền 3" },
  ];

  const FALLBACK_EVAL_QUICK = [
    { id: "m01_basic_a", icon: "📦", text: "Basic", cap: "di chuyển cơ bản" },
    { id: "m04_obstacle_wall", icon: "🧱", text: "Vật cản", cap: "A* đi vòng tường" },
    { id: "m07_pickdrop_far", icon: "🔄", text: "Gắp/thả", cap: "pick xa → drop" },
    { id: "m09_language_case", icon: "🔤", text: "Ngôn ngữ", cap: "chữ hoa/thường" },
    { id: "t10_replan_detour", icon: "🚧", text: "Replan", cap: "đổi đường vòng" },
    { id: "t13_safety_at_dest", icon: "🛑", text: "An toàn", cap: "người chắn đích" },
    { id: "m10_infeasible_missing", icon: "⛔", text: "Bất khả thi", cap: "hàng không có" },
    { id: "t17_robustness_vague", icon: "❓", text: "Mơ hồ", cap: "agent hỏi lại" },
  ];

  global.ScenariosUI = {
    fetchCatalog,
    populateSelect,
    buildEvalChips,
    applyGoal,
    getGoalText,
    getById: (id) => byId[id],
    get catalog() { return catalog; },
  };
})(window);
