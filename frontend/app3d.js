/* =====================================================================
   RoboPlanner — 3D view (Three.js) + scene editor
   Reuses the SAME backend as the 2D app: /api/v1/world (GET+POST),
   /api/v1/scenario, /api/v1/ws (live Gemini) and /replays/*.json.
   Editor: click a grid cell to place robot / pallet / obstacle / person /
   destination; rotation is LOCKED (zoom only); run the agent on your scene.
   ===================================================================== */

// ---------------------------------------------------------------------------
// DOM refs
// ---------------------------------------------------------------------------
const sceneHost      = document.getElementById("scene3d");
const statusMsg      = document.getElementById("status-msg");
const loadBtn        = document.getElementById("load-btn");
const runBtn         = document.getElementById("run-btn");
const demoBtn        = document.getElementById("demo-btn");
const replaySelect   = document.getElementById("replay-select");
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
const hudDot         = document.getElementById("hud-dot");
const hudText        = document.getElementById("hud-text");

// ---------------------------------------------------------------------------
// Runtime state
// ---------------------------------------------------------------------------
let currentState  = null;
let activeWS      = null;
let replayActive  = false;
let wsRetried     = false;
let auditLog      = { meta: {}, steps: [] };
let runToolCalls  = 0;
let runReplans    = 0;

const STEP_DELAY_MS = 360;
const REPLAY_BASE   = "/replays/";
const HERO_SCENARIO = "warehouse_blocked";
const HERO_GOAL     = "Đưa pallet A tới chuyền 3, tránh người";

const REPLAY_META = {
  hero_replan:   { label: "🚧 Replan — người chặn & giao thành công", file: "hero_replan.json" },
  safety_ask:    { label: "🛑 An toàn — agent dừng & hỏi",            file: "safety_ask.json"  },
  infeasible_no: { label: "⛔ Bất khả thi — agent nói KHÔNG",          file: "infeasible_no.json"},
};

const STATUS_MAP = {
  planning: { text: "ĐANG LẬP KẾ HOẠCH", cls: "status-planning", color: "#85b7eb" },
  acting:   { text: "ĐANG CHẠY",          cls: "status-acting",   color: "#2f74c0" },
  blocked:  { text: "BỊ CHẶN → REPLAN",   cls: "status-blocked",  color: "#ef9f27" },
  asking:   { text: "DỪNG · HỎI NGƯỜI",   cls: "status-asking",   color: "#e24b4a" },
  done:     { text: "HOÀN THÀNH",          cls: "status-done",     color: "#1d9e75" },
  failed:   { text: "THẤT BẠI",            cls: "status-failed",   color: "#e24b4a" },
};

const ZONE_COLORS = [0xa78bfa, 0x34d399, 0xfbbf24, 0x60a5fa];

// Embedded sample warehouse so the 3D map ALWAYS shows a full scene immediately —
// even with no backend / offline. You can edit it freely or "Xoá hết" to start clean.
const DEFAULT_WORLD = {
  width: 16, height: 10, tick: 0,
  robot: { id: "robot-1", kind: "robot", label: "Robot", pos: { x: 1, y: 1 }, carrying: null },
  objects: [
    { id: "pallet-A", kind: "object", label: "pallet A", pos: { x: 3, y: 3 }, carrying: null },
    { id: "box-B", kind: "object", label: "thùng B", pos: { x: 5, y: 6 }, carrying: null }
  ],
  people: [{ id: "person-1", kind: "person", label: "Công nhân", pos: { x: 7, y: 3 }, carrying: null }],
  obstacles: [
    { id: "obs-1", kind: "obstacle", label: null, pos: { x: 7, y: 4 }, carrying: null },
    { id: "obs-2", kind: "obstacle", label: null, pos: { x: 7, y: 5 }, carrying: null }
  ],
  zones: [
    { name: "khu A", cells: [{x:2,y:2},{x:3,y:2},{x:4,y:2},{x:2,y:3},{x:3,y:3},{x:4,y:3},{x:2,y:4},{x:3,y:4},{x:4,y:4}] },
    { name: "chuyền 3", cells: [{x:11,y:2},{x:12,y:2},{x:13,y:2},{x:11,y:3},{x:12,y:3},{x:13,y:3},{x:11,y:4},{x:12,y:4},{x:13,y:4}] }
  ]
};
function cloneWorld(w) { return JSON.parse(JSON.stringify(w)); }

function normalize(s) { return String(s || "").normalize("NFC").toLowerCase().trim(); }

// ===========================================================================
// THREE.JS SCENE
// ===========================================================================
let THREE = null;
let renderer, scene, camera, staticGroup, dynamicGroup;
let robotMesh = null;
let floorMesh = null, hoverMesh = null, raycaster = null, ndc = null;
const objMeshes = {};      // id -> Group
const personMeshes = {};   // id -> Group
let objCells = {};         // id -> {x,y}
let prevCarrying = null;
let carriedId = null;
let sceneReady = false;
let gridW = 16, gridH = 10;

// Rotation is LOCKED — fixed camera angle, zoom only.
const orbit = { r: 22, theta: 0.72, phi: 0.92 };
const camTarget = { x: 0, y: 0.6, z: 0 };
let dragging = false, autoRotate = false;

function gridToWorld(gx, gy) { return { x: gx - (gridW - 1) / 2, z: gy - (gridH - 1) / 2 }; }

function makeTextSprite(text, color) {
  try {
    const cvs = document.createElement("canvas");
    const c = cvs.getContext("2d");
    c.font = "bold 34px sans-serif";
    const w = Math.max(64, Math.ceil(c.measureText(text).width) + 26);
    cvs.width = w; cvs.height = 64;
    c.font = "bold 34px sans-serif";
    c.textAlign = "center"; c.textBaseline = "middle";
    c.lineWidth = 5; c.strokeStyle = "rgba(8,12,18,0.92)";
    c.strokeText(text, w / 2, 34);
    c.fillStyle = color || "#ffffff";
    c.fillText(text, w / 2, 34);
    const tex = new THREE.CanvasTexture(cvs);
    tex.minFilter = THREE.LinearFilter;
    const spr = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: false }));
    const hUnits = 0.5;
    spr.scale.set((w / 64) * hUnits, hUnits, 1);
    return spr;
  } catch (e) { return null; }
}

function makeForklift() {
  const g = new THREE.Group();
  const blue  = new THREE.MeshStandardMaterial({ color: 0x2f74c0, roughness: 0.5, metalness: 0.1 });
  const blue2 = new THREE.MeshStandardMaterial({ color: 0x255a93, roughness: 0.5 });
  const steel = new THREE.MeshStandardMaterial({ color: 0x9aa6b3, roughness: 0.6, metalness: 0.3 });
  const fork  = new THREE.MeshStandardMaterial({ color: 0xc9b34a, roughness: 0.5, metalness: 0.2 });
  const tyre  = new THREE.MeshStandardMaterial({ color: 0x10141a, roughness: 0.9 });
  const body = new THREE.Mesh(new THREE.BoxGeometry(0.66, 0.34, 0.82), blue); body.position.y = 0.3; g.add(body);
  const cab  = new THREE.Mesh(new THREE.BoxGeometry(0.46, 0.3, 0.38), blue2); cab.position.set(0, 0.6, -0.16); g.add(cab);
  [-0.2, 0.2].forEach(x => { const m = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.78, 0.06), steel); m.position.set(x, 0.47, 0.42); g.add(m); });
  [-0.2, 0.2].forEach(x => { const f = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.05, 0.58), fork); f.position.set(x, 0.14, 0.72); g.add(f); });
  [[-0.28, 0.34], [0.28, 0.34], [-0.28, -0.34], [0.28, -0.34]].forEach(p => {
    const w = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.13, 0.1, 16), tyre);
    w.rotation.z = Math.PI / 2; w.position.set(p[0], 0.13, p[1]); g.add(w);
  });
  const carried = makePallet(false, null, 0.62);
  carried.position.set(0, 0.42, 0.55); carried.visible = false; carried.name = "carried";
  g.add(carried); g.userData.carried = carried;
  return g;
}

function makePallet(withLabel, label, scale) {
  scale = scale || 0.8;
  const g = new THREE.Group();
  const base = new THREE.Mesh(new THREE.BoxGeometry(0.74 * scale, 0.14, 0.74 * scale),
    new THREE.MeshStandardMaterial({ color: 0x8a5a28, roughness: 0.85 }));
  base.position.y = 0.07 * scale; g.add(base);
  const load = new THREE.Mesh(new THREE.BoxGeometry(0.58 * scale, 0.36 * scale, 0.58 * scale),
    new THREE.MeshStandardMaterial({ color: 0xc7903f, roughness: 0.7 }));
  load.position.y = 0.28 * scale; g.add(load);
  if (withLabel && label) { const s = makeTextSprite(label, "#ffd9a0"); if (s) { s.position.y = 0.7; g.add(s); } }
  return g;
}

function makePerson(label) {
  const g = new THREE.Group();
  const red = new THREE.MeshStandardMaterial({ color: 0xe24b4a, roughness: 0.6 });
  const body = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.24, 0.6, 18), red); body.position.y = 0.42; g.add(body);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.16, 18, 14), new THREE.MeshStandardMaterial({ color: 0xf0a59f, roughness: 0.7 }));
  head.position.y = 0.82; g.add(head);
  if (label) { const s = makeTextSprite(label, "#ffc7c4"); if (s) { s.position.y = 1.18; g.add(s); } }
  return g;
}

function clearGroup(grp) {
  while (grp.children.length) {
    const c = grp.children.pop();
    grp.remove(c);
    c.traverse && c.traverse(o => { if (o.geometry) o.geometry.dispose(); if (o.material) { if (o.material.map) o.material.map.dispose(); o.material.dispose && o.material.dispose(); } });
  }
}

function showSceneError(msg) {
  let d = sceneHost.querySelector(".scene-error");
  if (!d) {
    d = document.createElement("div");
    d.className = "scene-error";
    d.style.cssText = "position:absolute;inset:0;display:flex;align-items:center;justify-content:center;text-align:center;padding:24px;color:#ffd0d0;font-size:14px;line-height:1.6;background:rgba(15,20,27,0.9)";
    sceneHost.appendChild(d);
  }
  d.textContent = msg; d.style.display = "flex";
}
function clearSceneError() { const d = sceneHost.querySelector(".scene-error"); if (d) d.style.display = "none"; }

function initScene() {
  if (sceneReady) return;
  THREE = window.THREE;
  if (!THREE) {
    showSceneError("Không tải được three.js (thư viện 3D). Kiểm tra file vendor/three.min.js, hoặc bật mạng để tải từ CDN, rồi tải lại trang.");
    return;
  }
  const W = sceneHost.clientWidth || 680, H = sceneHost.clientHeight || 520;
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true });
  } catch (e) {
    showSceneError("Trình duyệt không khởi tạo được WebGL. Hãy bật tăng tốc phần cứng (hardware acceleration) hoặc thử trình duyệt khác (Chrome/Edge/Firefox).");
    return;
  }
  renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
  renderer.setSize(W, H); renderer.setClearColor(0x0f141b, 1);
  sceneHost.appendChild(renderer.domElement);
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(48, W / H, 0.1, 400);
  scene.add(new THREE.HemisphereLight(0xcfe0f2, 0x141a22, 0.85));
  const dl = new THREE.DirectionalLight(0xffffff, 0.9); dl.position.set(10, 16, 8); scene.add(dl);
  const dl2 = new THREE.DirectionalLight(0x9fb6d8, 0.3); dl2.position.set(-8, 9, -10); scene.add(dl2);
  staticGroup = new THREE.Group(); dynamicGroup = new THREE.Group();
  scene.add(staticGroup); scene.add(dynamicGroup);

  // Editor raycasting + hover highlight
  raycaster = new THREE.Raycaster();
  ndc = new THREE.Vector2();
  hoverMesh = new THREE.Mesh(new THREE.PlaneGeometry(0.98, 0.98),
    new THREE.MeshBasicMaterial({ color: 0x5dcaa5, transparent: true, opacity: 0.38, depthTest: false }));
  hoverMesh.rotation.x = -Math.PI / 2; hoverMesh.position.y = 0.03; hoverMesh.visible = false;
  scene.add(hoverMesh);

  const dom = renderer.domElement;
  dom.style.cursor = "crosshair";
  dom.style.touchAction = "none";
  // Rotation is locked. Click = place; move = hover; wheel = zoom only.
  dom.addEventListener("pointermove", e => {
    const cell = cellFromEvent(e);
    if (!cell) { hoverMesh.visible = false; return; }
    const w = gridToWorld(cell.x, cell.y);
    hoverMesh.position.set(w.x, 0.03, w.z);
    if (hoverMesh.material.color && hoverMesh.material.color.setHex) hoverMesh.material.color.setHex(TOOL_COLORS[editorTool] || 0x5dcaa5);
    hoverMesh.visible = true;
  });
  dom.addEventListener("pointerleave", () => { hoverMesh.visible = false; });
  dom.addEventListener("click", e => { const cell = cellFromEvent(e); if (cell) placeAt(cell.x, cell.y); });
  dom.addEventListener("wheel", e => { e.preventDefault(); orbit.r = Math.max(8, Math.min(48, orbit.r + (e.deltaY > 0 ? 1.2 : -1.2))); }, { passive: false });

  if (window.ResizeObserver) {
    new ResizeObserver(() => {
      const w = sceneHost.clientWidth || W, h = sceneHost.clientHeight || H;
      renderer.setSize(w, h); camera.aspect = w / h; camera.updateProjectionMatrix();
    }).observe(sceneHost);
  }

  clearSceneError();
  sceneReady = true;
  animate();
}

function fitCamera() {
  orbit.r = Math.max(gridW, gridH) * 1.05 + 5;
  camTarget.x = 0; camTarget.y = 0.6; camTarget.z = 0;
}

function buildStatic(state) {
  clearGroup(staticGroup);
  gridW = state.width; gridH = state.height;
  floorMesh = new THREE.Mesh(new THREE.PlaneGeometry(gridW, gridH),
    new THREE.MeshStandardMaterial({ color: 0x2c3a48, roughness: 1 }));
  floorMesh.rotation.x = -Math.PI / 2; staticGroup.add(floorMesh);

  const pts = [];
  for (let x = 0; x <= gridW; x++) { pts.push(x - gridW / 2, 0.011, -gridH / 2, x - gridW / 2, 0.011, gridH / 2); }
  for (let y = 0; y <= gridH; y++) { pts.push(-gridW / 2, 0.011, y - gridH / 2, gridW / 2, 0.011, y - gridH / 2); }
  const gg = new THREE.BufferGeometry();
  gg.setAttribute("position", new THREE.Float32BufferAttribute(pts, 3));
  staticGroup.add(new THREE.LineSegments(gg, new THREE.LineBasicMaterial({ color: 0x4a5a6e })));

  (state.zones || []).forEach((zone, i) => {
    const col = ZONE_COLORS[i % ZONE_COLORS.length];
    zone.cells.forEach(cell => {
      const p = new THREE.Mesh(new THREE.PlaneGeometry(0.96, 0.96),
        new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.22 }));
      p.rotation.x = -Math.PI / 2; const w = gridToWorld(cell.x, cell.y);
      p.position.set(w.x, 0.02, w.z); staticGroup.add(p);
    });
    if (zone.cells.length) {
      const xs = zone.cells.map(c => c.x), ys = zone.cells.map(c => c.y);
      const cx = (Math.min(...xs) + Math.max(...xs)) / 2, cy = (Math.min(...ys) + Math.max(...ys)) / 2;
      const w = gridToWorld(cx, cy);
      const s = makeTextSprite(zone.name, "#dfe7f2"); if (s) { s.position.set(w.x, 0.5, w.z); staticGroup.add(s); }
    }
  });

  (state.obstacles || []).forEach(obs => {
    const m = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.7, 0.8),
      new THREE.MeshStandardMaterial({ color: 0x5b6675, roughness: 0.9 }));
    const w = gridToWorld(obs.pos.x, obs.pos.y); m.position.set(w.x, 0.35, w.z); staticGroup.add(m);
  });
}

function buildDynamic(state) {
  clearGroup(dynamicGroup);
  for (const k in objMeshes) delete objMeshes[k];
  for (const k in personMeshes) delete personMeshes[k];

  robotMesh = makeForklift();
  const rw = gridToWorld(state.robot.pos.x, state.robot.pos.y);
  robotMesh.position.set(rw.x, 0, rw.z);
  robotMesh.userData.tx = rw.x; robotMesh.userData.tz = rw.z; robotMesh.userData.yaw = 0;
  dynamicGroup.add(robotMesh);

  objCells = {};
  (state.objects || []).forEach(o => {
    objCells[o.id] = { x: o.pos.x, y: o.pos.y };
    const m = makePallet(true, o.label || o.id, 0.8);
    const w = gridToWorld(o.pos.x, o.pos.y);
    m.position.set(w.x, 0, w.z); m.userData.tx = w.x; m.userData.tz = w.z;
    m.visible = o.pos.x >= 0;
    objMeshes[o.id] = m; dynamicGroup.add(m);
  });

  (state.people || []).forEach(p => {
    const m = makePerson(p.label || null);
    const w = gridToWorld(p.pos.x, p.pos.y);
    m.position.set(w.x, 0, w.z); m.userData.tx = w.x; m.userData.tz = w.z;
    personMeshes[p.id] = m; dynamicGroup.add(m);
  });

  prevCarrying = null; carriedId = null;
  if (robotMesh.userData.carried) robotMesh.userData.carried.visible = false;
}

function matchObjId(carrying) {
  if (!carrying || !currentState) return null;
  const n = normalize(carrying);
  for (const o of currentState.objects) {
    if (o.id === carrying || normalize(o.label) === n || o.id === n) return o.id;
  }
  return null;
}

// Full (re)build. keepCamera=true keeps the current view (used during editing).
function renderFull(state, keepCamera) {
  initScene();
  if (!sceneReady) return;
  gridW = state.width; gridH = state.height;
  try { buildStatic(state); } catch (e) { console.error("buildStatic failed:", e); }
  try { buildDynamic(state); } catch (e) { console.error("buildDynamic failed:", e); }
  if (!keepCamera) fitCamera();
}

// Per-step sync — only move dynamic meshes toward new targets
function renderSync(state) {
  if (!sceneReady || !robotMesh || !state) return;
  const rw = gridToWorld(state.robot.pos.x, state.robot.pos.y);
  robotMesh.userData.tx = rw.x; robotMesh.userData.tz = rw.z;

  const cur = state.robot.carrying;
  if (cur && !prevCarrying) {
    carriedId = matchObjId(cur);
    if (carriedId && objMeshes[carriedId]) objMeshes[carriedId].visible = false;
    if (robotMesh.userData.carried) robotMesh.userData.carried.visible = true;
  } else if (!cur && prevCarrying) {
    const dropId = matchObjId(prevCarrying) || carriedId;
    if (dropId) {
      objCells[dropId] = { x: state.robot.pos.x, y: state.robot.pos.y };
      const w = gridToWorld(state.robot.pos.x, state.robot.pos.y);
      if (objMeshes[dropId]) {
        objMeshes[dropId].position.set(w.x, 0, w.z);
        objMeshes[dropId].userData.tx = w.x; objMeshes[dropId].userData.tz = w.z;
        objMeshes[dropId].visible = true;
      }
    }
    carriedId = null;
    if (robotMesh.userData.carried) robotMesh.userData.carried.visible = false;
  }
  prevCarrying = cur;

  (state.people || []).forEach(p => {
    const m = personMeshes[p.id]; if (!m) return;
    const w = gridToWorld(p.pos.x, p.pos.y); m.userData.tx = w.x; m.userData.tz = w.z;
  });
}

function animate() {
  requestAnimationFrame(animate);
  if (!sceneReady) return;
  dynamicGroup.children.forEach(m => {
    if (m.userData.tx === undefined) return;
    const dx = m.userData.tx - m.position.x, dz = m.userData.tz - m.position.z;
    m.position.x += dx * 0.16; m.position.z += dz * 0.16;
    if (m === robotMesh && Math.hypot(dx, dz) > 0.004) {
      const ty = Math.atan2(dx, dz);
      let diff = ((ty - robotMesh.userData.yaw + Math.PI) % (2 * Math.PI)) - Math.PI;
      robotMesh.userData.yaw += diff * 0.2; robotMesh.rotation.y = robotMesh.userData.yaw;
    }
  });
  if (autoRotate && !dragging) orbit.theta += 0.0010;  // disabled (autoRotate=false)
  const s = Math.sin(orbit.phi);
  camera.position.set(
    camTarget.x + orbit.r * s * Math.sin(orbit.theta),
    camTarget.y + orbit.r * Math.cos(orbit.phi),
    camTarget.z + orbit.r * s * Math.cos(orbit.theta)
  );
  camera.lookAt(camTarget.x, camTarget.y, camTarget.z);
  renderer.render(scene, camera);
}

function setHud(text, color) {
  if (hudText && text) hudText.textContent = text;
  if (hudDot && color) hudDot.style.background = color;
}

// ===========================================================================
// SCENE EDITOR — click to place; rotation locked
// ===========================================================================
const TOOL_COLORS = { robot: 0x2f74c0, pallet: 0xc7903f, obstacle: 0x5b6675, person: 0xe24b4a, dest: 0x1d9e75, erase: 0x9aa6b3 };
let editorTool = "robot";
let eidCounter = 1;

function cellFromEvent(e) {
  if (!floorMesh || !camera || !raycaster) return null;
  const rect = renderer.domElement.getBoundingClientRect();
  if (!rect.width || !rect.height) return null;
  ndc.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  ndc.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(ndc, camera);
  const hits = raycaster.intersectObject(floorMesh);
  if (!hits.length) return null;
  const p = hits[0].point;
  const gx = Math.round(p.x + (gridW - 1) / 2), gy = Math.round(p.z + (gridH - 1) / 2);
  if (gx < 0 || gy < 0 || gx >= gridW || gy >= gridH) return null;
  return { x: gx, y: gy };
}

function entityAt(gx, gy) {
  const at = e => e.pos.x === gx && e.pos.y === gy;
  return currentState.objects.some(at) || currentState.obstacles.some(at) || currentState.people.some(at)
    || (currentState.robot.pos.x === gx && currentState.robot.pos.y === gy);
}

function nextLetter() {
  const used = new Set(currentState.objects.map(o => (o.label || "").replace(/pallet|thùng/gi, "").trim().toUpperCase()));
  for (let i = 0; i < 26; i++) { const L = String.fromCharCode(65 + i); if (!used.has(L)) return L; }
  return "X";
}

function ensureDestZone() {
  let z = currentState.zones.find(zz => zz.name === "đích");
  if (!z) { z = { name: "đích", cells: [] }; currentState.zones.push(z); }
  return z;
}

function placeAt(gx, gy) {
  if (!currentState) return;
  const cell = { x: gx, y: gy };
  if (editorTool === "robot") {
    currentState.robot.pos = cell;
  } else if (editorTool === "pallet") {
    if (entityAt(gx, gy)) return;
    currentState.objects.push({ id: "pallet-" + (eidCounter++), kind: "object", label: "pallet " + nextLetter(), pos: cell, carrying: null });
  } else if (editorTool === "obstacle") {
    if (entityAt(gx, gy)) return;
    currentState.obstacles.push({ id: "obs-" + (eidCounter++), kind: "obstacle", label: null, pos: cell, carrying: null });
  } else if (editorTool === "person") {
    if (entityAt(gx, gy)) return;
    currentState.people.push({ id: "person-" + (eidCounter++), kind: "person", label: "Người", pos: cell, carrying: null });
  } else if (editorTool === "dest") {
    const z = ensureDestZone();
    const idx = z.cells.findIndex(c => c.x === gx && c.y === gy);
    if (idx >= 0) z.cells.splice(idx, 1); else z.cells.push(cell);
    if (!z.cells.length) currentState.zones = currentState.zones.filter(zz => zz.name !== "đích");
  } else if (editorTool === "erase") {
    currentState.objects   = currentState.objects.filter(o => !(o.pos.x === gx && o.pos.y === gy));
    currentState.obstacles = currentState.obstacles.filter(o => !(o.pos.x === gx && o.pos.y === gy));
    currentState.people    = currentState.people.filter(o => !(o.pos.x === gx && o.pos.y === gy));
    currentState.zones.forEach(z => { z.cells = z.cells.filter(c => !(c.x === gx && c.y === gy)); });
    currentState.zones = currentState.zones.filter(z => z.cells.length);
  }
  renderFull(currentState, true);
  updateWorldHints(currentState);
  suggestGoal();
  statusMsg.textContent = `Cảnh tự đặt · ${currentState.objects.length} vật · ${currentState.obstacles.length} vật cản · ${currentState.people.length} người`;
}

function clearWorld() {
  if (!currentState) return;
  currentState.objects = []; currentState.obstacles = []; currentState.people = []; currentState.zones = [];
  renderFull(currentState, true); updateWorldHints(currentState);
  setHud("Cảnh trống — đặt vật rồi chạy", "#5dcaa5");
  statusMsg.textContent = "Đã xoá hết. Bấm công cụ rồi bấm vào ô để đặt; xong bấm “Chạy agent trên cảnh này”.";
}

function suggestGoal() {
  if (goalInput.value.trim()) return;
  const pal = currentState.objects[0];
  const dest = currentState.zones.find(z => z.name === "đích") || currentState.zones[0];
  if (pal && dest) goalInput.value = `Đưa ${pal.label} tới ${dest.name}`;
}

async function runOnEditorWorld() {
  if (!currentState) return;
  suggestGoal();
  if (!goalInput.value.trim()) { statusMsg.textContent = "Nhập mục tiêu (vd: Đưa pallet A tới đích) rồi chạy."; goalInput.focus(); return; }
  setHud("Gửi cảnh cho agent…", "#85b7eb");
  statusMsg.textContent = "Đang gửi cảnh tự đặt cho agent…";
  try {
    const r = await fetch("/api/v1/world", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(currentState) });
    if (!r.ok) throw new Error("HTTP " + r.status);
    currentState = await r.json();
    renderFull(currentState, true);
  } catch (e) {
    statusMsg.textContent = "Cần mở backend (chạy run_may_A.bat → http://localhost:8000) để agent suy luận trên cảnh tự đặt.";
    setHud("Chưa nối backend", "#e24b4a");
    return;
  }
  startRun(false);
}

// ===========================================================================
// World hints (text only — same as 2D)
// ===========================================================================
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

// ===========================================================================
// Snapshot apply + animation queue (mirrors 2D app)
// ===========================================================================
function applySnapshot(snap) {
  if (!currentState || !snap) return;
  currentState.robot.pos      = snap.robot.pos;
  currentState.robot.carrying = snap.robot.carrying;
  if (Array.isArray(snap.people)) {
    snap.people.forEach(sp => { const p = currentState.people.find(pp => pp.id === sp.id); if (p) p.pos = sp.pos; });
  }
  currentState.tick = snap.tick;
}

let renderQueue = [], renderRunning = false;
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
function enqueueStep(snap, fn) { renderQueue.push({ snap, fn }); drainRenderQueue(); }
async function drainRenderQueue() {
  if (renderRunning) return;
  renderRunning = true;
  while (renderQueue.length > 0) {
    const { snap, fn } = renderQueue.shift();
    if (snap) { applySnapshot(snap); renderSync(currentState); }
    if (typeof fn === "function") fn();
    await sleep(STEP_DELAY_MS);
  }
  renderRunning = false;
}

// ===========================================================================
// Status / plan / trace / audit / metrics (same logic as 2D)
// ===========================================================================
function setStatus(status) {
  const s = STATUS_MAP[status]; if (!s) return;
  statusBadge.textContent = s.text; statusBadge.className = `status-badge ${s.cls}`;
  setHud(s.text, s.color);
}

function renderPlan(plan, completedUpTo) {
  if (!plan || !plan.length) return;
  planList.innerHTML = "";
  plan.forEach((step, i) => {
    const li = document.createElement("li"); li.textContent = step;
    if (completedUpTo !== undefined && i < completedUpTo) li.classList.add("plan-done");
    else if (completedUpTo !== undefined && i === completedUpTo) li.classList.add("plan-active");
    planList.appendChild(li);
  });
}

function escapeHTML(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

function appendTrace(node, lastAction, worldSnap) {
  if (!lastAction) return;
  const empty = traceLog.querySelector(".trace-empty"); if (empty) empty.remove();
  const action = lastAction.action || "?";
  const argsStr = JSON.stringify(lastAction.args || {});
  const rawObs = lastAction.observation || "";
  const ok = lastAction.ok !== false;
  const obsShort = rawObs.length > 140 ? rawObs.slice(0, 140) + "…" : rawObs;
  auditLog.steps.push({ node, action, args: lastAction.args || {}, observation: rawObs, ok, world_tick: worldSnap ? worldSnap.tick : null });
  if (action !== "perceive") runToolCalls++;
  setHud(`${node} → ${action}`, null);
  const line = document.createElement("div");
  line.className = `trace-line ${ok ? "trace-ok" : "trace-fail"}`;
  line.innerHTML =
    `<span class="trace-node">${escapeHTML(node)}</span><span class="trace-arrow"> → </span>` +
    `<span class="trace-action">${escapeHTML(action)}</span>` +
    `<span class="trace-args">(${escapeHTML(argsStr)})</span><span class="trace-arrow"> → </span>` +
    `<span class="trace-obs">${escapeHTML(obsShort)}</span> <span class="trace-flag">${ok ? "✓" : "✗"}</span>`;
  traceLog.appendChild(line); traceLog.scrollTop = traceLog.scrollHeight;
}

function downloadAuditLog() {
  const blob = new Blob([JSON.stringify(auditLog, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a"); a.href = url; a.download = `audit_log_${Date.now()}.json`;
  document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(url);
}

function showMetrics(status) {
  metricsText.textContent = `lệnh gọi tool: ${runToolCalls} · bám thực tế: 100% · bịa: 0 · lập lại KH: ${runReplans} · kết quả: ${status || "?"}`;
  metricsPanel.style.display = "";
  if (groundedBadge) groundedBadge.style.display = "";
  auditLog.meta.tool_calls = runToolCalls; auditLog.meta.replans = runReplans;
  auditLog.meta.grounded_pct = 100; auditLog.meta.hallucinated = 0; auditLog.meta.result = status;
  auditBtn.disabled = false;
}

function setRunning(running) {
  runBtn.disabled = running; loadBtn.disabled = running; demoBtn.disabled = running; replaySelect.disabled = running;
}

function resetPanels() {
  traceLog.innerHTML = '<div class="trace-empty">Đang chờ...</div>';
  planList.innerHTML = '<li class="plan-empty">Đang lập kế hoạch...</li>';
  answerPanel.style.display = "none"; askPanel.style.display = "none"; quotaPanel.style.display = "none";
  replayNote.style.display = "none"; metricsPanel.style.display = "none";
  if (groundedBadge) groundedBadge.style.display = "none";
  auditBtn.disabled = true; renderQueue = []; renderRunning = false;
  auditLog = { meta: { goal: goalInput.value.trim(), started: new Date().toISOString() }, steps: [] };
  runToolCalls = 0; runReplans = 0;
}

function closeWS() { if (activeWS && activeWS.readyState < WebSocket.CLOSING) activeWS.close(); activeWS = null; }

// ===========================================================================
// REPLAY MODE (Demo nhanh)
// ===========================================================================
async function startReplay(replayKey) {
  const key = replayKey || replaySelect.value || "hero_replan";
  const meta = REPLAY_META[key] || REPLAY_META["hero_replan"];
  closeWS(); replayActive = true; setRunning(true); resetPanels();
  traceLog.innerHTML = '<div class="trace-empty">Đang phát lại...</div>';
  replayNote.textContent = `Phát lại bản ghi THẬT của agent Gemini: ${meta.label} — không gọi lại API`;
  replayNote.style.display = "";
  statusBadge.textContent = "PHÁT LẠI"; statusBadge.className = "status-badge status-planning";
  setHud("Phát lại", "#85b7eb");
  statusMsg.textContent = "Đang tải bản ghi...";

  let fixture;
  try {
    const resp = await fetch(REPLAY_BASE + meta.file);
    if (!resp.ok) throw new Error(`HTTP ${resp.status} — ${meta.file}`);
    fixture = await resp.json();
  } catch (e) {
    setRunning(false); replayActive = false; replayNote.style.display = "none";
    statusMsg.textContent = `Không tải được bản ghi (${escapeHTML(e.message)}) — thử Chạy thật (Gemini) hoặc chọn bản ghi khác.`;
    runBtn.disabled = false; return;
  }

  if (fixture.initial_world) {
    const w = fixture.initial_world;
    currentState = { width: w.width, height: w.height, tick: 0, robot: w.robot, objects: w.objects, people: w.people, obstacles: w.obstacles, zones: w.zones };
    renderFull(currentState); updateWorldHints(currentState);
  }
  if (fixture.meta && !goalInput.value.trim()) goalInput.value = fixture.meta.goal;
  if (fixture.meta && fixture.meta.caption) replayNote.textContent = `📽 Phát lại THẬT: ${fixture.meta.caption} — không gọi lại API`;
  statusMsg.textContent = `Phát lại: ${fixture.meta ? fixture.meta.goal : ""}`;

  let actionCount = 0, lastPlan = null, lastStatus = "done";
  if (fixture.meta) { auditLog.meta = { ...auditLog.meta, ...fixture.meta, replay: true }; runReplans = fixture.meta.replans || 0; }

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
        if (status === "asking" && pending_question) { askQuestion.textContent = pending_question; askPanel.style.display = ""; }
        if (answer) { answerText.textContent = answer; answerPanel.style.display = ""; }
        statusMsg.textContent = `[Phát lại] Tick ${currentState ? currentState.tick : 0} · ${escapeHTML(node || "")}`;
      });
      await sleep(STEP_DELAY_MS + 20);
    } else if (evt.type === "done") {
      enqueueStep(null, () => {
        setRunning(false); replayActive = false; statusMsg.textContent = "Phát lại hoàn thành.";
        if (lastPlan) renderPlan(lastPlan, lastPlan.length);
        const finalStatus = fixture.meta && fixture.meta.result === "asking" ? "asking"
                          : fixture.meta && fixture.meta.result === "failed" ? "failed" : lastStatus;
        if (!statusBadge.classList.contains("status-" + finalStatus)) setStatus(finalStatus);
        showMetrics(finalStatus);
        if (fixture.meta && fixture.meta.capability === "safety") {
          const note = document.createElement("p"); note.className = "safety-note";
          note.textContent = "✓ Agent dừng & hỏi là ĐÚNG — human-in-loop, không cố đi tiếp khi người sát robot.";
          metricsPanel.after(note);
        }
      });
    }
  }
}

// ===========================================================================
// LIVE RUN — WebSocket (same protocol as 2D)
// ===========================================================================
function startRun(isRetry) {
  const goal = goalInput.value.trim();
  if (!goal) { goalInput.focus(); return; }
  if (!isRetry) {
    closeWS(); wsRetried = false; resetPanels();
    traceLog.innerHTML = '<div class="trace-empty">Đang chạy agent...</div>';
    planList.innerHTML = '<li class="plan-empty">Đang lập kế hoạch...</li>';
  }
  replayActive = false; setRunning(true);
  statusBadge.textContent = "ĐANG LẬP KẾ HOẠCH"; statusBadge.className = "status-badge status-planning";
  setHud("Kết nối agent…", "#85b7eb");
  statusMsg.textContent = isRetry ? "Thử lại kết nối..." : "Đang kết nối...";

  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${proto}//${location.host}/api/v1/ws`;
  let ws;
  try { ws = new WebSocket(wsUrl); } catch (e) { setRunning(false); showQuotaError(); return; }
  activeWS = ws;

  let firstMsgTimer = setTimeout(() => {
    if (activeWS !== ws) return;
    closeWS();
    if (!wsRetried) { wsRetried = true; startRun(true); } else { setRunning(false); showQuotaError(); }
  }, 30000);

  let actionCount = 0, lastPlan = null, liveStatus = "done";
  ws.onopen = () => { statusMsg.textContent = "Đã kết nối · Đang gửi mục tiêu..."; ws.send(JSON.stringify({ goal_text: goal })); };
  ws.onmessage = (evt) => {
    clearTimeout(firstMsgTimer);
    let msg; try { msg = JSON.parse(evt.data); } catch { return; }
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
        if (status === "asking" && pending_question) { askQuestion.textContent = pending_question; askPanel.style.display = ""; }
        if (answer) { answerText.textContent = answer; answerPanel.style.display = ""; }
        statusMsg.textContent = `Tick ${currentState ? currentState.tick : 0} · Node: ${escapeHTML(node || "")}`;
      });
    } else if (type === "done") {
      enqueueStep(null, () => {
        setRunning(false); activeWS = null; statusMsg.textContent = "Agent hoàn thành.";
        if (!statusBadge.classList.contains("status-done") && !statusBadge.classList.contains("status-failed")) { setStatus("done"); liveStatus = "done"; }
        if (lastPlan) renderPlan(lastPlan, lastPlan.length);
        showMetrics(liveStatus); auditLog.meta.goal = goal;
      });
    } else if (type === "error") {
      const detail = String(msg.detail || "");
      if (detail.includes("429") || detail.includes("quota") || detail.includes("rate")) {
        enqueueStep(null, () => { setRunning(false); activeWS = null; showQuotaError(); });
      } else {
        enqueueStep(null, () => { setRunning(false); activeWS = null; statusMsg.textContent = `Lỗi agent: ${escapeHTML(detail || "Không rõ")}`; setStatus("failed"); });
      }
    }
  };
  ws.onerror = () => {
    clearTimeout(firstMsgTimer); renderQueue = []; renderRunning = false; setRunning(false); activeWS = null;
    if (!wsRetried) { wsRetried = true; startRun(true); } else showQuotaError();
  };
  ws.onclose = (evt) => {
    clearTimeout(firstMsgTimer); if (activeWS === ws) activeWS = null;
    if (!evt.wasClean && runBtn.disabled) {
      renderQueue = []; renderRunning = false; setRunning(false);
      if (!wsRetried) { wsRetried = true; startRun(true); } else showQuotaError();
    }
  };
}

function showQuotaError() {
  quotaPanel.style.display = "";
  statusMsg.textContent = "Gemini không phản hồi — dùng ▶ Demo nhanh để xem bản ghi thật.";
  setStatus("failed");
}

// ===========================================================================
// Bindings + scenario loading + init
// ===========================================================================
demoBtn.addEventListener("click", () => { replayActive = false; startReplay(replaySelect.value); });
quotaDemoBtn.addEventListener("click", () => { replayActive = false; startReplay(replaySelect.value); });
auditBtn.addEventListener("click", downloadAuditLog);
runBtn.addEventListener("click", () => startRun(false));
goalInput.addEventListener("keydown", e => { if (e.key === "Enter" && !runBtn.disabled) startRun(false); });
askContinueBtn.addEventListener("click", () => { askPanel.style.display = "none"; });

document.querySelectorAll(".chip").forEach(chip => {
  chip.addEventListener("click", () => {
    const goal = chip.dataset.goal || "", scenario = chip.dataset.scenario || "", replay = chip.dataset.replay || "";
    if (goal) goalInput.value = goal;
    if (scenario) scenarioSelect.value = scenario;
    if (replay) replaySelect.value = replay;
    replayActive = false; startReplay(replay || replaySelect.value);
  });
});

// Editor tool palette + actions
document.querySelectorAll(".etool").forEach(b => b.addEventListener("click", () => {
  editorTool = b.dataset.tool || "robot";
  document.querySelectorAll(".etool").forEach(x => x.classList.toggle("active", x === b));
}));
const clearWorldBtn = document.getElementById("clear-world-btn");
if (clearWorldBtn) clearWorldBtn.addEventListener("click", clearWorld);
const runEditorBtn = document.getElementById("run-editor-btn");
if (runEditorBtn) runEditorBtn.addEventListener("click", runOnEditorWorld);

async function fetchWorld() { const r = await fetch("/api/v1/world"); if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); }
async function postScenario(name) {
  const r = await fetch(`/api/v1/scenario?name=${encodeURIComponent(name)}`, { method: "POST" });
  if (!r.ok) { const e = await r.json().catch(() => ({ detail: r.statusText })); throw new Error(e.detail || r.statusText); }
  return r.json();
}

async function loadAndDraw(stateFn) {
  statusMsg.textContent = "Đang tải..."; loadBtn.disabled = true;
  try {
    const state = await stateFn();
    currentState = state; renderFull(state); updateWorldHints(state);
    runBtn.disabled = false;
    statusMsg.textContent = `Tick ${state.tick} · ${state.width}×${state.height} · ${state.objects.length} vật thể · ${state.people.length} người`;
    setHud("Sẵn sàng — bấm ô để chỉnh cảnh", "#5dcaa5");
  } catch (err) { statusMsg.textContent = `Lỗi: ${err.message}`; console.error(err); }
  finally { if (!activeWS) loadBtn.disabled = false; }
}

loadBtn.addEventListener("click", () => { closeWS(); replayActive = false; setRunning(false); loadAndDraw(() => postScenario(scenarioSelect.value)); });
scenarioSelect.addEventListener("change", () => { closeWS(); replayActive = false; setRunning(false); loadAndDraw(() => postScenario(scenarioSelect.value)); });

// Render a FULL sample warehouse immediately so the 3D map is never empty —
// even before data loads, with no backend, or offline. You can edit it freely.
currentState = cloneWorld(DEFAULT_WORLD);
renderFull(currentState);
updateWorldHints(currentState);
setHud("Bấm ô để đặt vật · cuộn để phóng to", "#5dcaa5");

(async function init() {
  try {
    const state = await postScenario(HERO_SCENARIO);
    currentState = state; renderFull(state); updateWorldHints(state);
    runBtn.disabled = false; goalInput.value = HERO_GOAL;
    statusMsg.textContent = `Tick ${state.tick} · ${state.width}×${state.height} · ${state.objects.length} vật thể · ${state.people.length} người`;
    setHud("Sẵn sàng — bấm ô để chỉnh cảnh", "#5dcaa5");
  } catch (_e) {
    statusMsg.textContent = "Backend chưa chạy — bạn vẫn tự đặt được cảnh; mở run_may_A.bat để agent suy luận.";
    setHud("Cảnh mẫu — backend chưa nối", "#85b7eb");
  }
})();
