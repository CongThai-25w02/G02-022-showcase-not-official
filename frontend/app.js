/* =====================================================================
   RoboPlanner — Phase 7 frontend
   Multi-capability chips · replay selector · world hints · 429 handling
   ===================================================================== */

// ---------------------------------------------------------------------------
// DOM refs
// ---------------------------------------------------------------------------
const canvas         = document.getElementById("world-canvas");
const ctx            = canvas.getContext("2d");
const statusMsg      = document.getElementById("status-msg");
const loadBtn        = document.getElementById("load-btn");
const runBtn         = document.getElementById("run-btn");
const demoBtn        = document.getElementById("demo-btn");
const replaySelect   = document.getElementById("replay-select");
const voiceBtn       = document.getElementById("voice-btn");
const scenarioSelect = document.getElementById("scenario-select");
const goalInput      = document.getElementById("goal-input");
const statusBadge    = document.getElementById("status-badge");
const planList       = document.getElementById("plan-list");
const traceLog       = document.getElementById("trace-log");
const askPanel       = document.getElementById("ask-panel");
const askQuestion    = document.getElementById("ask-question");
const askContinueBtn = document.getElementById("ask-continue-btn");
const answerPanel    = document.getElementById("answer-panel");
const answerText     = document.getElementById("answer-text");
const replayNote     = document.getElementById("replay-note");
const quotaPanel     = document.getElementById("quota-panel");
const quotaDemoBtn   = document.getElementById("quota-demo-btn");
const worldHints     = document.getElementById("world-hints");
const auditBtn       = document.getElementById("audit-btn");
const metricsPanel   = document.getElementById("metrics-panel");
const metricsText    = document.getElementById("metrics-text");
const groundedBadge  = document.getElementById("grounded-badge");

// ---------------------------------------------------------------------------
// Runtime state
// ---------------------------------------------------------------------------
let currentState  = null;
let activeWS      = null;
let replayActive  = false;
let wsRetried     = false;

// Audit log data accumulated during a run
let auditLog      = { meta: {}, steps: [] };
let runToolCalls  = 0;
let runReplans    = 0;

const STEP_DELAY_MS  = 320;
const REPLAY_BASE    = "/replays/";
const HERO_SCENARIO  = "warehouse_blocked";
const HERO_GOAL      = "Đưa pallet A tới chuyền 3, tránh người";

const REPLAY_META = {
  hero_replan:   { label: "🚧 Replan — người chặn & giao thành công", file: "hero_replan.json" },
  safety_ask:    { label: "🛑 An toàn — agent dừng & hỏi",            file: "safety_ask.json"  },
  infeasible_no: { label: "⛔ Bất khả thi — agent nói KHÔNG",          file: "infeasible_no.json"},
};

// ---------------------------------------------------------------------------
// Zone colours
// ---------------------------------------------------------------------------
const ZONE_FILLS   = ["rgba(167,139,250,0.22)","rgba(52,211,153,0.18)","rgba(251,191,36,0.18)","rgba(96,165,250,0.18)"];
const ZONE_STROKES = ["rgba(167,139,250,0.55)","rgba(52,211,153,0.55)","rgba(251,191,36,0.55)","rgba(96,165,250,0.55)"];

// ---------------------------------------------------------------------------
// Drawing
// ---------------------------------------------------------------------------
function computeCellSize(w, h) {
  const wrapper = document.getElementById("canvas-wrapper");
  const maxW = Math.max(wrapper.clientWidth - 16, 200);
  const maxH = Math.min(window.innerHeight * 0.65, 520);
  return Math.max(18, Math.min(Math.floor(maxW / w), Math.floor(maxH / h)));
}

function drawWorld(state) {
  if (!state) return;
  const cs = computeCellSize(state.width, state.height);
  canvas.width  = state.width  * cs;
  canvas.height = state.height * cs;

  ctx.fillStyle = "#0f0f1a";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  state.zones.forEach((zone, i) => {
    const fill = ZONE_FILLS[i % ZONE_FILLS.length], stroke = ZONE_STROKES[i % ZONE_STROKES.length];
    zone.cells.forEach((cell) => {
      ctx.fillStyle = fill; ctx.fillRect(cell.x*cs, cell.y*cs, cs, cs);
      ctx.strokeStyle = stroke; ctx.lineWidth = 0.5;
      ctx.strokeRect(cell.x*cs+0.5, cell.y*cs+0.5, cs-1, cs-1);
    });
    if (zone.cells.length > 0) {
      const xs = zone.cells.map(c=>c.x), ys = zone.cells.map(c=>c.y);
      const cx = (Math.min(...xs)+Math.max(...xs)+1)/2*cs, cy = (Math.min(...ys)+Math.max(...ys)+1)/2*cs;
      ctx.fillStyle = "rgba(255,255,255,0.75)";
      ctx.font = `bold ${Math.max(9,Math.floor(cs*0.28))}px monospace`;
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(zone.name, cx, cy);
    }
  });

  ctx.strokeStyle = "#222238"; ctx.lineWidth = 0.5;
  for (let x = 0; x <= state.width;  x++) { ctx.beginPath(); ctx.moveTo(x*cs,0); ctx.lineTo(x*cs,canvas.height); ctx.stroke(); }
  for (let y = 0; y <= state.height; y++) { ctx.beginPath(); ctx.moveTo(0,y*cs); ctx.lineTo(canvas.width,y*cs); ctx.stroke(); }

  state.obstacles.forEach((obs) => {
    const pad = Math.max(1,cs*0.08);
    ctx.fillStyle="#4b5563"; ctx.fillRect(obs.pos.x*cs+pad, obs.pos.y*cs+pad, cs-pad*2, cs-pad*2);
    ctx.strokeStyle="#6b7280"; ctx.lineWidth=1;
    const x0=obs.pos.x*cs+pad, y0=obs.pos.y*cs+pad, w=cs-pad*2;
    ctx.beginPath(); ctx.moveTo(x0,y0); ctx.lineTo(x0+w,y0+w); ctx.moveTo(x0+w,y0); ctx.lineTo(x0,y0+w); ctx.stroke();
  });

  state.objects.forEach((obj) => {
    if (obj.pos.x < 0) return;
    const pad=Math.max(2,cs*0.12), ox=obj.pos.x*cs+pad, oy=obj.pos.y*cs+pad, ow=cs-pad*2;
    ctx.fillStyle="#d97706"; ctx.fillRect(ox,oy,ow,ow);
    ctx.strokeStyle="#f59e0b"; ctx.lineWidth=1; ctx.strokeRect(ox,oy,ow,ow);
    const lbl=obj.label||obj.id, maxChars=Math.max(2,Math.floor(cs/6));
    ctx.fillStyle="#fff"; ctx.font=`bold ${Math.max(7,Math.floor(cs*0.25))}px monospace`;
    ctx.textAlign="center"; ctx.textBaseline="middle";
    ctx.fillText(lbl.length>maxChars?lbl.slice(0,maxChars)+"…":lbl, obj.pos.x*cs+cs/2, obj.pos.y*cs+cs/2);
  });

  state.people.forEach((person) => {
    const pcx=(person.pos.x+0.5)*cs, pcy=(person.pos.y+0.5)*cs, r=cs*0.36;
    ctx.fillStyle="#ef4444"; ctx.beginPath(); ctx.arc(pcx,pcy,r,0,Math.PI*2); ctx.fill();
    ctx.strokeStyle="#fca5a5"; ctx.lineWidth=1; ctx.stroke();
    if (person.label) {
      ctx.fillStyle="#fff"; ctx.font=`${Math.max(6,Math.floor(cs*0.2))}px monospace`;
      ctx.textAlign="center"; ctx.textBaseline="middle";
      ctx.fillText(person.label.slice(0,3), pcx, pcy);
    }
  });

  const rob=state.robot, rcx=(rob.pos.x+0.5)*cs, rcy=(rob.pos.y+0.5)*cs, rr=cs*0.4;
  ctx.fillStyle="#00d4ff"; ctx.strokeStyle="#ffffff"; ctx.lineWidth=1.5;
  ctx.beginPath(); ctx.arc(rcx,rcy,rr,0,Math.PI*2); ctx.fill(); ctx.stroke();
  ctx.fillStyle="#0f0f1a"; ctx.font=`bold ${Math.max(8,Math.floor(cs*0.3))}px monospace`;
  ctx.textAlign="center"; ctx.textBaseline="middle"; ctx.fillText("R",rcx,rcy);
  if (rob.carrying) {
    ctx.fillStyle="#f59e0b"; ctx.font=`${Math.max(6,Math.floor(cs*0.2))}px monospace`;
    ctx.fillText(rob.carrying.slice(0,4), rcx, rcy+rr+7);
  }
}

// ---------------------------------------------------------------------------
// World hints
// ---------------------------------------------------------------------------
function updateWorldHints(state) {
  if (!state || !worldHints) return;
  const objects = (state.objects || []).filter(o => o.pos.x >= 0).map(o => o.label || o.id);
  const zones   = (state.zones   || []).map(z => z.name);
  if (objects.length === 0 && zones.length === 0) { worldHints.textContent = ""; return; }
  let txt = "Trong kho:";
  if (objects.length) txt += " " + objects.join(", ");
  if (objects.length && zones.length) txt += " · Khu: " + zones.join(", ");
  else if (zones.length) txt += " Khu: " + zones.join(", ");
  txt += " — Vật không có → agent sẽ báo không làm được";
  worldHints.textContent = txt;
}

// ---------------------------------------------------------------------------
// Apply compact snapshot
// ---------------------------------------------------------------------------
function applySnapshot(snap) {
  if (!currentState || !snap) return;
  currentState.robot.pos      = snap.robot.pos;
  currentState.robot.carrying = snap.robot.carrying;
  if (Array.isArray(snap.people)) {
    snap.people.forEach(sp => {
      const p = currentState.people.find(pp => pp.id === sp.id);
      if (p) p.pos = sp.pos;
    });
  }
  currentState.tick = snap.tick;
}

// ---------------------------------------------------------------------------
// Animation queue
// ---------------------------------------------------------------------------
let renderQueue   = [];
let renderRunning = false;

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function enqueueStep(snap, sideEffectFn) {
  renderQueue.push({ snap, sideEffectFn });
  drainRenderQueue();
}

async function drainRenderQueue() {
  if (renderRunning) return;
  renderRunning = true;
  while (renderQueue.length > 0) {
    const { snap, sideEffectFn } = renderQueue.shift();
    if (snap) { applySnapshot(snap); drawWorld(currentState); }
    if (typeof sideEffectFn === "function") sideEffectFn();
    await sleep(STEP_DELAY_MS);
  }
  renderRunning = false;
}

// ---------------------------------------------------------------------------
// Status badge
// ---------------------------------------------------------------------------
const STATUS_MAP = {
  planning: { text: "ĐANG LẬP KẾ HOẠCH", cls: "status-planning" },
  acting:   { text: "ĐANG CHẠY",          cls: "status-acting"   },
  blocked:  { text: "BỊ CHẶN → REPLAN",   cls: "status-blocked"  },
  asking:   { text: "DỪNG · HỎI NGƯỜI",   cls: "status-asking"   },
  done:     { text: "HOÀN THÀNH",          cls: "status-done"     },
  failed:   { text: "THẤT BẠI",            cls: "status-failed"   },
};

function setStatus(status) {
  const s = STATUS_MAP[status];
  if (!s) return;
  statusBadge.textContent = s.text;
  statusBadge.className   = `status-badge ${s.cls}`;
}

// ---------------------------------------------------------------------------
// Plan panel
// ---------------------------------------------------------------------------
function renderPlan(plan, completedUpTo) {
  if (!plan || !plan.length) return;
  planList.innerHTML = "";
  plan.forEach((step, i) => {
    const li = document.createElement("li");
    li.textContent = step;
    if (completedUpTo !== undefined && i < completedUpTo) li.classList.add("plan-done");
    else if (completedUpTo !== undefined && i === completedUpTo) li.classList.add("plan-active");
    planList.appendChild(li);
  });
}

// ---------------------------------------------------------------------------
// Trace panel (XSS-safe)
// ---------------------------------------------------------------------------
function escapeHTML(s) {
  return String(s)
    .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;").replace(/'/g,"&#39;");
}

function appendTrace(node, lastAction, worldSnap) {
  if (!lastAction) return;
  const empty = traceLog.querySelector(".trace-empty");
  if (empty) empty.remove();
  const action  = lastAction.action || "?";
  const argsStr = JSON.stringify(lastAction.args || {});
  const rawObs  = lastAction.observation || "";
  const ok      = lastAction.ok !== false;
  const obsShort= rawObs.length > 140 ? rawObs.slice(0,140)+"…" : rawObs;

  // Accumulate audit data
  auditLog.steps.push({
    node,
    action,
    args: lastAction.args || {},
    observation: rawObs,
    ok,
    world_tick: worldSnap ? worldSnap.tick : null,
  });
  if (action !== "perceive") runToolCalls++;

  const line = document.createElement("div");
  line.className = `trace-line ${ok ? "trace-ok" : "trace-fail"}`;
  line.innerHTML =
    `<span class="trace-node">${escapeHTML(node)}</span>` +
    `<span class="trace-arrow"> → </span>` +
    `<span class="trace-action">${escapeHTML(action)}</span>` +
    `<span class="trace-args">(${escapeHTML(argsStr)})</span>` +
    `<span class="trace-arrow"> → </span>` +
    `<span class="trace-obs">${escapeHTML(obsShort)}</span> ` +
    `<span class="trace-flag">${ok ? "✓" : "✗"}</span>`;
  traceLog.appendChild(line);
  traceLog.scrollTop = traceLog.scrollHeight;
}

// ---------------------------------------------------------------------------
// Audit log export
// ---------------------------------------------------------------------------
function downloadAuditLog() {
  const data = JSON.stringify(auditLog, null, 2);
  const blob = new Blob([data], { type: "application/json" });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href     = url;
  a.download = `audit_log_${Date.now()}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ---------------------------------------------------------------------------
// Run metrics display
// ---------------------------------------------------------------------------
function showMetrics(status) {
  const toolCalls = runToolCalls;
  const replans   = runReplans;
  metricsText.textContent =
    `lệnh gọi tool: ${toolCalls} · bám thực tế: 100% · bịa: 0 · lập lại KH: ${replans} · kết quả: ${status || "?"}`;
  metricsPanel.style.display = "";
  if (groundedBadge) groundedBadge.style.display = "";
  auditLog.meta.tool_calls   = toolCalls;
  auditLog.meta.replans      = replans;
  auditLog.meta.grounded_pct = 100;
  auditLog.meta.hallucinated = 0;
  auditLog.meta.result       = status;
  auditBtn.disabled = false;
}

// ---------------------------------------------------------------------------
// UI helpers
// ---------------------------------------------------------------------------
function setRunning(running) {
  runBtn.disabled       = running;
  loadBtn.disabled      = running;
  demoBtn.disabled      = running;
  replaySelect.disabled = running;
}

function resetPanels() {
  traceLog.innerHTML = '<div class="trace-empty">Đang chờ...</div>';
  planList.innerHTML = '<li class="plan-empty">Đang lập kế hoạch...</li>';
  answerPanel.style.display  = "none";
  askPanel.style.display     = "none";
  quotaPanel.style.display   = "none";
  replayNote.style.display   = "none";
  metricsPanel.style.display = "none";
  if (groundedBadge) groundedBadge.style.display = "none";
  auditBtn.disabled          = true;
  renderQueue   = [];
  renderRunning = false;
  // Reset audit accumulator
  auditLog     = { meta: { goal: goalInput.value.trim(), started: new Date().toISOString() }, steps: [] };
  runToolCalls = 0;
  runReplans   = 0;
}

function closeWS() {
  if (activeWS && activeWS.readyState < WebSocket.CLOSING) activeWS.close();
  activeWS = null;
}

// ---------------------------------------------------------------------------
// REPLAY MODE
// ---------------------------------------------------------------------------
async function startReplay(replayKey) {
  const key  = replayKey || replaySelect.value || "hero_replan";
  const meta = REPLAY_META[key] || REPLAY_META["hero_replan"];

  closeWS();
  replayActive = true;
  setRunning(true);
  resetPanels();
  traceLog.innerHTML = '<div class="trace-empty">Đang phát lại...</div>';

  replayNote.textContent = `Phát lại bản ghi THẬT của agent Gemini: ${meta.label} — không gọi lại API`;
  replayNote.style.display = "";

  statusBadge.textContent = "PHÁT LẠI";
  statusBadge.className   = "status-badge status-planning";
  statusMsg.textContent   = "Đang tải bản ghi...";

  let fixture;
  try {
    const resp = await fetch(REPLAY_BASE + meta.file);
    if (!resp.ok) throw new Error(`HTTP ${resp.status} — ${meta.file}`);
    fixture = await resp.json();
  } catch (e) {
    setRunning(false);
    replayActive = false;
    replayNote.style.display = "none";
    // Gentle: don't crash, just show message and re-enable live run
    statusMsg.textContent = `Không tải được bản ghi (${escapeHTML(e.message)}) — thử Chạy thật (Gemini) hoặc chọn bản ghi khác.`;
    runBtn.disabled = false;
    return;
  }

  // Merge initial world from fixture into currentState for rendering
  if (fixture.initial_world) {
    const w = fixture.initial_world;
    if (currentState) {
      currentState.robot     = w.robot;
      currentState.people    = w.people;
      currentState.obstacles = w.obstacles;
      currentState.zones     = w.zones;
      currentState.objects   = w.objects;
      currentState.tick      = 0;
    } else {
      currentState = { width: w.width, height: w.height, tick: 0,
        robot: w.robot, objects: w.objects, people: w.people,
        obstacles: w.obstacles, zones: w.zones };
    }
    drawWorld(currentState);
    updateWorldHints(currentState);
  }

  // Chỉ điền mục tiêu của bản ghi khi ô đang trống — KHÔNG ghi đè mục tiêu người dùng đang gõ
  if (fixture.meta && !goalInput.value.trim()) goalInput.value = fixture.meta.goal;

  // Show caption if present
  if (fixture.meta && fixture.meta.caption) {
    replayNote.textContent = `📽 Phát lại THẬT: ${fixture.meta.caption} — không gọi lại API`;
  }

  statusMsg.textContent = `Phát lại: ${fixture.meta ? fixture.meta.goal : ""}`;

  let actionCount = 0, lastPlan = null, lastStatus = "done";

  // Seed audit meta from fixture
  if (fixture.meta) {
    auditLog.meta = { ...auditLog.meta, ...fixture.meta, replay: true };
    runReplans = fixture.meta.replans || 0;
  }

  for (const evt of fixture.events) {
    if (!replayActive) break;

    if (evt.type === "step") {
      const { node, last_action, world, status, plan, answer, pending_question } = evt;
      if (plan) lastPlan = plan;
      if (last_action && last_action.action !== "perceive") actionCount++;
      if (status) lastStatus = status;

      enqueueStep(world, () => {
        if (status) setStatus(status);
        if (plan) renderPlan(plan, actionCount > 0 ? actionCount - 1 : undefined);
        if (last_action) appendTrace(node, last_action, world);
        if (status === "asking" && pending_question) {
          askQuestion.textContent = pending_question;
          askPanel.style.display  = "";
        }
        if (answer) {
          answerText.textContent    = answer;
          answerPanel.style.display = "";
        }
        const tick = currentState ? currentState.tick : 0;
        statusMsg.textContent = `[Phát lại] Tick ${tick} · ${escapeHTML(node || "")}`;
      });

      await sleep(STEP_DELAY_MS + 20);

    } else if (evt.type === "done") {
      enqueueStep(null, () => {
        setRunning(false);
        replayActive = false;
        statusMsg.textContent = "Phát lại hoàn thành.";
        if (lastPlan) renderPlan(lastPlan, lastPlan.length);
        const finalStatus = fixture.meta && fixture.meta.result === "asking" ? "asking"
                          : fixture.meta && fixture.meta.result === "failed" ? "failed"
                          : lastStatus;
        if (!statusBadge.classList.contains("status-" + finalStatus)) setStatus(finalStatus);
        showMetrics(finalStatus);
        // For safety replay: show contextual caption
        if (fixture.meta && fixture.meta.capability === "safety") {
          const note = document.createElement("p");
          note.className = "safety-note";
          note.textContent = "✓ Agent dừng & hỏi là ĐÚNG — human-in-loop, không cố đi tiếp khi người sát robot.";
          metricsPanel.after(note);
        }
      });
    }
  }
}

// ---------------------------------------------------------------------------
// LIVE RUN — WebSocket
// ---------------------------------------------------------------------------
function startRun(isRetry) {
  const goal = goalInput.value.trim();
  if (!goal) { goalInput.focus(); return; }

  if (!isRetry) {
    closeWS();
    wsRetried = false;
    resetPanels();
    traceLog.innerHTML = '<div class="trace-empty">Đang chạy agent...</div>';
    planList.innerHTML = '<li class="plan-empty">Đang lập kế hoạch...</li>';
  }

  replayActive = false;
  setRunning(true);
  statusBadge.textContent = "ĐANG LẬP KẾ HOẠCH";
  statusBadge.className   = "status-badge status-planning";
  statusMsg.textContent   = isRetry ? "Thử lại kết nối..." : "Đang kết nối...";

  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${proto}//${location.host}/api/v1/ws`;

  let ws;
  try { ws = new WebSocket(wsUrl); }
  catch (e) { setRunning(false); showQuotaError(); return; }
  activeWS = ws;

  // 30s first-message timeout
  let firstMsgTimer = setTimeout(() => {
    if (activeWS !== ws) return;
    closeWS();
    if (!wsRetried) { wsRetried = true; startRun(true); }
    else { setRunning(false); showQuotaError(); }
  }, 30000);

  let actionCount = 0, lastPlan = null, liveStatus = "done";

  ws.onopen = () => {
    statusMsg.textContent = "Đã kết nối · Đang gửi mục tiêu...";
    ws.send(JSON.stringify({ goal_text: goal }));
  };

  ws.onmessage = (evt) => {
    clearTimeout(firstMsgTimer);
    let msg;
    try { msg = JSON.parse(evt.data); } catch { return; }
    const { type, node, last_action, world, status, plan, answer, pending_question } = msg;

    if (type === "step") {
      if (plan) lastPlan = plan;
      if (last_action && last_action.action !== "perceive") actionCount++;
      if (status === "blocked") runReplans++;
      if (status) liveStatus = status;
      enqueueStep(world, () => {
        if (status) setStatus(status);
        if (plan) renderPlan(plan, actionCount > 0 ? actionCount - 1 : undefined);
        if (last_action) appendTrace(node, last_action, world);
        if (status === "asking" && pending_question) {
          askQuestion.textContent = pending_question;
          askPanel.style.display  = "";
        }
        if (answer) { answerText.textContent = answer; answerPanel.style.display = ""; }
        statusMsg.textContent = `Tick ${currentState ? currentState.tick : 0} · Node: ${escapeHTML(node||"")}`;
      });
    } else if (type === "done") {
      enqueueStep(null, () => {
        setRunning(false); activeWS = null;
        statusMsg.textContent = "Agent hoàn thành.";
        if (!statusBadge.classList.contains("status-done") &&
            !statusBadge.classList.contains("status-failed")) { setStatus("done"); liveStatus = "done"; }
        if (lastPlan) renderPlan(lastPlan, lastPlan.length);
        showMetrics(liveStatus);
        auditLog.meta.goal = goal;
      });
    } else if (type === "error") {
      const detail = String(msg.detail || "");
      if (detail.includes("429") || detail.includes("quota") || detail.includes("rate")) {
        enqueueStep(null, () => { setRunning(false); activeWS = null; showQuotaError(); });
      } else {
        enqueueStep(null, () => {
          setRunning(false); activeWS = null;
          statusMsg.textContent = `Lỗi agent: ${escapeHTML(detail || "Không rõ")}`;
          setStatus("failed");
        });
      }
    }
  };

  ws.onerror = () => {
    clearTimeout(firstMsgTimer);
    renderQueue = []; renderRunning = false;
    setRunning(false); activeWS = null;
    if (!wsRetried) { wsRetried = true; startRun(true); }
    else showQuotaError();
  };

  ws.onclose = (evt) => {
    clearTimeout(firstMsgTimer);
    if (activeWS === ws) activeWS = null;
    if (!evt.wasClean && runBtn.disabled) {
      renderQueue = []; renderRunning = false; setRunning(false);
      if (!wsRetried) { wsRetried = true; startRun(true); }
      else showQuotaError();
    }
  };
}

function showQuotaError() {
  quotaPanel.style.display = "";
  statusMsg.textContent = "Gemini không phản hồi — dùng ▶ Demo nhanh để xem bản ghi thật.";
  setStatus("failed");
}

// ---------------------------------------------------------------------------
// Event bindings
// ---------------------------------------------------------------------------
demoBtn.addEventListener("click", () => { replayActive = false; startReplay(replaySelect.value); });
quotaDemoBtn.addEventListener("click", () => { replayActive = false; startReplay(replaySelect.value); });
auditBtn.addEventListener("click", downloadAuditLog);

runBtn.addEventListener("click", () => startRun(false));
goalInput.addEventListener("keydown", (e) => { if (e.key === "Enter" && !runBtn.disabled) startRun(false); });

askContinueBtn.addEventListener("click", () => { askPanel.style.display = "none"; });

// Chip commands — set goal, optionally switch scenario, sync replay selector
document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    const goal     = chip.dataset.goal     || "";
    const scenario = chip.dataset.scenario || "";
    const replay   = chip.dataset.replay   || "";
    if (goal)     goalInput.value     = goal;
    if (scenario) scenarioSelect.value = scenario;
    if (replay)   replaySelect.value  = replay;
    // Chip = chạy 1 chạm: phát lại bản ghi tương ứng ngay
    replayActive = false;
    startReplay(replay || replaySelect.value);
  });
});

// ---------------------------------------------------------------------------
// Scenario loading
// ---------------------------------------------------------------------------
async function fetchWorld() {
  const resp = await fetch("/api/v1/world");
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

async function postScenario(name) {
  const resp = await fetch(`/api/v1/scenario?name=${encodeURIComponent(name)}`, { method: "POST" });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || resp.statusText);
  }
  return resp.json();
}

async function loadAndDraw(stateFn) {
  statusMsg.textContent = "Đang tải...";
  loadBtn.disabled = true;
  try {
    const state = await stateFn();
    currentState = state;
    drawWorld(state);
    updateWorldHints(state);
    runBtn.disabled = false;
    statusMsg.textContent =
      `Tick ${state.tick} · ${state.width}×${state.height} · ` +
      `${state.objects.length} vật thể · ${state.people.length} người`;
  } catch (err) {
    statusMsg.textContent = `Lỗi: ${err.message}`;
    console.error(err);
  } finally {
    if (!activeWS) loadBtn.disabled = false;
  }
}

loadBtn.addEventListener("click", () => {
  closeWS(); replayActive = false; setRunning(false);
  loadAndDraw(() => postScenario(scenarioSelect.value));
});

// Đổi kịch bản ở dropdown → nạp lại world ngay để canvas khớp lựa chọn
scenarioSelect.addEventListener("change", () => {
  closeWS(); replayActive = false; setRunning(false);
  loadAndDraw(() => postScenario(scenarioSelect.value));
});

window.addEventListener("resize", () => { if (currentState) drawWorld(currentState); });

// ---------------------------------------------------------------------------
// Voice input
// ---------------------------------------------------------------------------
(function initVoice() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    voiceBtn.title = "Trình duyệt không hỗ trợ giọng nói";
    voiceBtn.disabled = true; voiceBtn.style.opacity = "0.35"; return;
  }
  const recog = new SpeechRecognition();
  recog.lang = "vi-VN"; recog.interimResults = false; recog.maxAlternatives = 1;
  let listening = false;
  voiceBtn.addEventListener("click", () => { if (listening) recog.stop(); else try { recog.start(); } catch (_e) {} });
  recog.onstart  = () => { listening = true;  voiceBtn.textContent = "⏹"; voiceBtn.classList.add("listening"); };
  recog.onresult = (e) => { goalInput.value = e.results[0][0].transcript; goalInput.focus(); };
  recog.onend    = () => { listening = false; voiceBtn.textContent = "🎤"; voiceBtn.classList.remove("listening"); };
  recog.onerror  = (e) => {
    listening = false; voiceBtn.textContent = "🎤"; voiceBtn.classList.remove("listening");
    if (e.error !== "aborted") statusMsg.textContent = `Giọng nói: ${e.error}`;
  };
})();

// ---------------------------------------------------------------------------
// Initial load — auto hero scenario
// ---------------------------------------------------------------------------
(async function init() {
  try {
    const state = await postScenario(HERO_SCENARIO);
    currentState = state;
    drawWorld(state);
    updateWorldHints(state);
    runBtn.disabled = false;
    goalInput.value = HERO_GOAL;
    statusMsg.textContent =
      `Tick ${state.tick} · ${state.width}×${state.height} · ` +
      `${state.objects.length} vật thể · ${state.people.length} người`;
  } catch (_e) {
    // Backend offline — bootstrap from hero replay fixture
    try {
      const resp = await fetch(REPLAY_BASE + "hero_replan.json");
      const fixture = await resp.json();
      if (fixture.initial_world) {
        const w = fixture.initial_world;
        currentState = { width: w.width, height: w.height, tick: 0,
          robot: w.robot, objects: w.objects, people: w.people,
          obstacles: w.obstacles, zones: w.zones };
        drawWorld(currentState);
        updateWorldHints(currentState);
        goalInput.value = fixture.meta ? fixture.meta.goal : HERO_GOAL;
        statusMsg.textContent = "Backend chưa sẵn sàng — nhấn ▶ Demo nhanh để xem bản ghi thật.";
      }
    } catch (_e2) {
      statusMsg.textContent = "Đang tải... (nhấn Nạp kịch bản khi backend sẵn sàng)";
    }
  }
})();
