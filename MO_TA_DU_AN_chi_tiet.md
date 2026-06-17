# MÔ TẢ CHI TIẾT DỰ ÁN — AI20K‑162 Task‑Planner Agent (RoboPlanner)

> **HƯỚNG DẪN CHO AI (Gemini):** Đây là bản mô tả đầy đủ một dự án phần mềm. Hãy dùng tài liệu này để tạo ra **(1) một bản BÁO CÁO** (report kỹ thuật, mạch lạc, có mục lục, dùng cho nộp môn/đồ án) và **(2) một bộ SLIDE thuyết trình** (10–14 slide, dùng cho demo day ~5–7 phút). Yêu cầu:
> - Viết bằng **tiếng Việt**, giọng văn kỹ thuật nhưng dễ hiểu, trung thực (không thổi phồng).
> - Báo cáo: có Tóm tắt (abstract), Đặt vấn đề, Giải pháp, Kiến trúc, Triển khai, Đánh giá, Hạn chế & Hướng phát triển, Kết luận.
> - Slide: mỗi slide có tiêu đề + 3–5 gạch đầu dòng + gợi ý hình/biểu đồ. Có slide kiến trúc (mô tả sơ đồ), slide demo, slide kết quả đánh giá.
> - Giữ nguyên tính **trung thực**: thế giới là *mô phỏng 2D*, *agent là thật* (LLM). Nêu rõ phần đã làm vs phần ngoài phạm vi.
> - Phần "Số liệu đánh giá" có lưu ý quan trọng ở mục 9 — đọc kỹ trước khi trình bày con số.

---

## 1. Tóm tắt một dòng

**Vận hành viên ra lệnh bằng tiếng Việt** → **một agent LLM tự lập kế hoạch và điều khiển robot di chuyển đúng một vật thể** tới đích trong một **kho mô phỏng 2D xác định (deterministic)**, kết quả được **một oracle độc lập chấm điểm** (chống "ảo tưởng hoàn thành"), toàn bộ quá trình **minh bạch và có người trong vòng lặp**.

- **Tên sản phẩm:** RoboPlanner — "Lập kế hoạch tác vụ kho bằng AI agent".
- **Mã đề tài:** AI20K‑162 (Lập kế hoạch tác vụ) **gộp** AI20K‑161 (Điều khiển bằng ngôn ngữ tự nhiên).
- **Bối cảnh:** đồ án ~2 tuần, chỉ có laptop + điện thoại, **không có phần cứng robot** → robot được **mô phỏng 2D**, còn **agent là thật** (LLM lập kế hoạch + gọi tool thật, đọc kết quả thật từ sim).

---

## 2. Vấn đề (Problem)

Điều khiển robot kho hiện nay cứng nhắc và khó mở rộng:

1. **Rào cản ngôn ngữ ↔ lập trình:** Vận hành viên (không phải kỹ sư) không thể "ra lệnh" cho robot bằng ngôn ngữ thường — mọi nhiệm vụ phải được kỹ sư lập trình từng bước.
2. **Môi trường động:** Khi có người, xe nâng, vật cản xuất hiện, kịch bản lập sẵn bị hỏng và phải lập trình lại bằng tay.
3. **Hộp đen:** Không biết robot định làm gì, có an toàn không → khó tin tưởng, khó kiểm chứng, khó audit.

---

## 3. Giải pháp (Solution)

Một **agent lập kế hoạch** (LLM + tool‑calling) đứng giữa *ngôn ngữ* và *hành động*:

- **Feature 1 — Ra lệnh tiếng Việt tự nhiên (161):** ví dụ *"Đưa pallet A từ khu A sang chuyền 3"* → agent hiểu và thực thi.
- **Feature 2 — Lập kế hoạch + tự điều chỉnh (162):** phân rã mục tiêu thành chuỗi hành động, thực thi từng bước, **replan** khi bị chặn.
- **Feature 3 — Minh bạch + human‑in‑the‑loop:** hiển thị **kế hoạch + trace lý luận** (suy nghĩ → gọi tool → quan sát kết quả); khi **gặp người đứng sát / không chắc chắn**, agent **dừng và hỏi** thay vì đoán liều.

**Điểm khác biệt cốt lõi (định vị sản phẩm):** Hệ thống được thiết kế để **kiểm chứng được** — môi trường mô phỏng *tất định*, có **bất biến trạng thái** tự kiểm tra sau mỗi thao tác, và **oracle độc lập** chấm điểm thành công thay vì tin lời agent tự khai.

---

## 4. Người dùng mục tiêu (Target Users)

- **Chính:** vận hành viên kho/nhà máy muốn điều khiển robot bằng ngôn ngữ, không qua lập trình.
- **Phụ:** kỹ sư tích hợp robot (prototype nhanh logic nhiệm vụ); đội an toàn/QA cần kế hoạch minh bạch, kiểm chứng được.
- **Ngữ cảnh ứng dụng minh hoạ:** robot vận chuyển trong kho (ví dụ kho VinFast) — ra lệnh tiếng Việt, agent xử lý khi môi trường đổi, trace minh bạch để audit an toàn.

---

## 5. Phạm vi phiên bản v2 "thu nhỏ" (rất quan trọng để trình bày trung thực)

Sau phản hồi của mentor, nhóm **thu hẹp phạm vi** để chốt phần lõi *chắc chắn, kiểm chứng được* thay vì làm rộng mà hời hợt.

**TRỌNG TÂM (đã làm & đo):**
- Ra lệnh tiếng Việt → agent **lập kế hoạch và di chuyển ĐÚNG 1 vật thể** tới đích, qua kho có **chướng ngại tĩnh**, rồi **đặt đúng ô/đúng vùng** (được oracle xác nhận).
- Biết báo **"không làm được"** khi nhiệm vụ bất khả thi (vật không tồn tại / đích bị bịt kín).
- Trace từng bước + xuất log để audit.

**ĐÃ CẮT khỏi v2 (mã vẫn còn nhưng ngoài phạm vi đo — bật lại bằng cờ `core_scope=False`):**
- Replan khi gặp **người di chuyển động**; human‑in‑loop/an toàn ngữ nghĩa nâng cao; voice; đa vật thể/đa robot; lớp an toàn cứng (LiDAR/cảm biến); cầu nối sim→real (ROS/perception).

> Thông điệp trung thực để nhấn mạnh: *"Chúng tôi không khoe những gì chưa đo được. Phần lõi nhỏ nhưng đúng và chứng minh được."*

---

## 6. Công nghệ sử dụng (Tech Stack)

| Lớp | Công nghệ | Vai trò |
|---|---|---|
| AI Agent | **LangGraph + LangChain** | Vòng lặp plan‑and‑execute + ReAct (máy trạng thái có điều kiện) |
| LLM | **Google Gemini** (cloud) **hoặc Ollama** (local, vd `qwen2.5:7b`) | Sinh kế hoạch + chọn tool (function‑calling). Đổi provider chỉ bằng 1 biến `.env` |
| Backend | **FastAPI + Python 3.11** | REST API + WebSocket streaming |
| Sim World | `World` engine Python (lưới 2D, thuật toán **A\***) | Môi trường "có thẩm quyền" — mọi tool đọc/ghi trạng thái thật ở đây |
| Frontend | **Canvas 2D** (`app.js`) + **3D Three.js** (`app3d.js`, có scene editor) | Render sim + robot + người; bảng kế hoạch/trace; responsive + dark mode |
| Realtime | **WebSocket** | Stream từng bước (suy nghĩ → tool → observation) + trạng thái world |
| Kiểm chứng | `invariants.py` (bất biến trạng thái) + `oracle.py` (chấm điểm độc lập) | Đảm bảo sim không bao giờ vào trạng thái phi lý; thành công chấm khách quan |
| Testing | **pytest** (+ hypothesis property‑based) | Test tools, world, graph, eval, bất biến |
| DevOps | **Docker + GitHub Actions + LangSmith** (AI logs) | CI, container hoá, trace prompt/tool calls |

---

## 7. Kiến trúc hệ thống (Architecture)

### 7.1. Sơ đồ tổng thể (mô tả để vẽ lại)

```
Vận hành viên ──(mục tiêu tiếng Việt)──▶ Frontend (canvas 2D / 3D + bảng trace)
        ▲                                     │  REST + WebSocket
        │ (render trạng thái world,           ▼
        │  kế hoạch, trace)              FastAPI (src/api/routes.py)
        │                                     │
        │                                     ▼
        │                          LangGraph Agent (src/agents/graph.py)
        │                              │            │
        │              function‑calling│            │ gọi 9 tool
        │                              ▼            ▼
        │                        Gemini/Ollama   World sim Python (grid · A* · robot · objects · people · zones)
        └──────────────────────────────────────────┘
                                                 │
                                                 ▼
                                          LangSmith (AI logs / trace)
```

### 7.2. Vòng lặp agent (LangGraph state machine)

Agent là một **đồ thị trạng thái** gồm các node, với các cạnh có điều kiện:

```
START
  └─▶ parse_goal      : NL tiếng Việt → JSON {target, destination, constraints}
        └─▶ perceive   : đọc world → cập nhật world_view
              └─▶ plan : LLM sinh danh sách bước (≤10 bước)
                    └─▶ act      : LLM chọn & gọi ĐÚNG 1 tool / bước
                          └─▶ observe : đọc kết quả thật, cập nhật world_view, quyết định nhánh
                                ├─(còn việc)──────────────▶ act        (vòng lặp)
                                ├─(bị chặn, người ở xa)───▶ replan ─▶ act
                                ├─(người sát robot/mơ hồ)─▶ status=asking ─▶ summarize  (dừng & hỏi)
                                ├─(vượt giới hạn bước)────▶ cap ─▶ summarize
                                └─(đạt mục tiêu)──────────▶ summarize ─▶ END
```

**Chi tiết từng node (file `src/agents/nodes/`):**
- `parse_goal.py` — LLM bóc tách mục tiêu tiếng Việt thành JSON có cấu trúc; chịu lỗi (fallback nếu JSON hỏng).
- `perceive_node.py` — gọi tool `perceive`, nạp `world_view` vào state.
- `plan_node.py` — LLM sinh kế hoạch dạng mảng chuỗi mô tả bước (tối đa 10 bước).
- `act_node.py` — LLM được `bind_tools(ALL_TOOLS)`, **chỉ thực thi tool đầu tiên** mỗi lượt (nguyên tắc *1 hành động = 1 bước*); ghi `{action, args, observation, ok}` vào history.
- `observe_node.py` — phân tích kết quả bước cuối:
  - Nếu agent gọi `done` → **chỉ chấp nhận nếu mục tiêu thực sự đạt** (kiểm vật có đúng ở vùng đích & robot không còn mang gì); nếu chưa → bắt agent tiếp tục (chống khai khống).
  - Nếu `move_to` bị chặn bởi **người đứng kề ngay từ đầu** → chuyển sang `asking` (dừng & hỏi — an toàn).
  - Nếu bị chặn bởi người **ở xa** → `blocked` (sẽ replan).
- `replan_node.py` — LLM lập kế hoạch mới khi bị chặn (đi vòng / chờ / hỏi người); có **trần số lần replan** (`max_replans`, mặc định 5).
- `summarize_node.py` — sinh câu trả lời cuối + tóm tắt trace.
- `routing.py` — hàm thuần `decide_observe_route()` tách riêng để **unit‑test được**; chứa cờ `core_scope` (khi bật = phạm vi v2: gặp chặn thì KẾT THÚC thay vì replan).
- `graph.py` — lắp ráp đồ thị; node `cap` đánh dấu `failed` khi vượt `max_steps` (mặc định 40).

**Trạng thái agent (`state.py`, `AgentState`):** `goal_text, goal, plan, history, world_view, status, replans, steps, answer, pending_question`.

### 7.3. Lớp Tool — 9 primitive (file `src/agents/tools/tools.py`)

Mọi tool đọc/ghi **World singleton thật** — *không bịa kết quả*.

| Nhóm | Tool | Chức năng |
|---|---|---|
| Tri giác (read‑only) | `perceive()` | Quan sát toàn cảnh: robot, objects, people, obstacles, zones, tick |
| | `locate_object(label)` | Tìm vật theo nhãn (khớp mờ: bỏ dấu, không phân biệt hoa/thường); trả vị trí + vùng + tương đối so với robot |
| | `check_path(x, y)` | Kiểm tra đường tới ô đích có thông không; nếu nghẽn, chỉ ra người/vật chặn |
| Hành động (mutate) | `move_to(x, y)` | Di chuyển theo đường A* tránh vật cản tĩnh; **dừng ngay nếu ô kế có người** |
| | `pick(id_or_label)` | Nhặt vật ở cùng ô hoặc kề (Manhattan ≤ 1) |
| | `drop(x, y)` | Đặt vật đang mang xuống ô đích (có kiểm tra hợp lệ: không ra ngoài lưới, không lên vật cản) |
| Meta / an toàn | `wait(ticks)` | Chờ một số tick rồi quan sát lại (người có thể đã đi) |
| | `ask_human(question)` | Dừng và hỏi vận hành viên khi bất định / người chắn lối |
| | `done(summary)` | Khai báo hoàn thành + tóm tắt (nhưng oracle mới là người quyết định thật sự đạt hay chưa) |

### 7.4. World engine (file `src/services/world.py`)

- **Lưới 2D** (mặc định 16×10), các thực thể: `robot, objects, people, obstacles, zones`, có `tick`.
- **Tìm đường A\*** hai biến thể:
  - `astar()` — tránh cả vật cản tĩnh **và** người.
  - `astar_static()` — chỉ tránh vật cản tĩnh (dùng để robot bước từng ô, gặp người thì dừng).
- **Mutation an toàn:** `move_robot_to`, `pick_object`, `drop_at`, `advance_tick` (kích hoạt sự kiện động theo kịch bản). Sau **mỗi** mutation gọi `_verify()` → `assert_invariants()`.
- Đo **quãng đường đã đi** (`distance_traveled`) phục vụ tính SPL (hiệu quả đường đi).
- Khớp tên tiếng Việt mờ (NFC + casefold) qua `_normalize()`.
- World là **singleton** ở backend; frontend (kể cả editor 3D) có thể `POST /world` để đặt cảnh tự dựng.

### 7.5. Bất biến trạng thái (file `src/services/invariants.py`) — điểm nhấn kỹ thuật

`assert_invariants()` mã hoá các thuộc tính **luôn đúng** sau mọi thao tác; tách rời khỏi World (chỉ đọc `WorldState` serialisable nên tái dùng được ở test/eval):
1. Lưới hợp lệ (width/height > 0, tick ≥ 0).
2. Robot trong lưới và **không** nằm trên vật cản.
3. Nhất quán "đang mang": nếu không mang gì thì **không** vật nào off‑grid; nếu mang `id` thì **đúng một** vật off‑grid tại `(-1,-1)` và đúng là vật đó.
4. Mọi vật on‑grid: trong lưới và không nằm trên vật cản.
5. Mọi người: trong lưới.

→ Nếu sim rơi vào trạng thái phi lý, hệ thống **ném lỗi ngay** thay vì âm thầm hỏng. Đây là "khoá an toàn" cho tính đúng đắn của mô phỏng.

### 7.6. Oracle chấm điểm độc lập (file `src/services/oracle.py`) — điểm nhấn kỹ thuật

`check_object_moved(world, object_key, dest)` trả `True` **⟺** vật đang nằm tại đích **VÀ** robot không còn mang gì — **độc lập** hoàn toàn với status agent tự khai. `dest` có thể là tên vùng (zone), toạ độ `(x,y)`, hoặc Cell. → Chống "ảo tưởng hoàn thành": agent nói `done` không có nghĩa là đạt; oracle mới quyết định.

---

## 8. Mô hình dữ liệu & API

### 8.1. Schemas (Pydantic, `src/models/schemas.py`)
- `Cell{x,y}`, `Entity{id, kind∈[robot|object|person|obstacle], label, pos, carrying}`, `Zone{name, cells[]}`.
- `WorldState{width, height, robot, objects[], people[], obstacles[], zones[], tick, task?}`.
- API: `RunRequest{goal_text}`, `RunResponse{plan[], history[], answer, status}`.

### 8.2. Định dạng kịch bản (scenario JSON) — ví dụ `m01_basic_a.json`
```json
{
  "width": 16, "height": 10, "tick": 0,
  "robot":   {"id":"robot-1","kind":"robot","pos":{"x":1,"y":1},"carrying":null},
  "objects": [{"id":"pallet-A","kind":"object","label":"pallet A","pos":{"x":3,"y":3}}],
  "obstacles": [], "people": [],
  "zones": [{"name":"chuyền 3","cells":[{"x":12,"y":2}, ...]}],
  "task": {
    "id": "m01_basic_a",
    "goal_text": "Đưa pallet A từ khu A sang chuyền 3",
    "category": "basic", "feasible": true,
    "success": {"object": "pallet A", "at_zone": "chuyền 3"},
    "dynamic": []
  }
}
```

### 8.3. API endpoints (`src/api/routes.py`)
| Method | Path | Mô tả |
|---|---|---|
| GET | `/health` | Health check `{ok:true}` |
| GET | `/api/v1/world` | Lấy trạng thái world hiện tại |
| POST | `/api/v1/world` | Đặt world từ cảnh người dùng dựng (editor 3D) |
| GET | `/api/v1/scenarios` | Danh sách kịch bản cho dropdown UI |
| POST | `/api/v1/scenario?name=...` | Nạp một kịch bản theo tên |
| POST | `/api/v1/run` | Nhận `{goal_text}` → chạy agent → trả `{plan, history, answer, status}` |
| WS | `/api/v1/ws` | Stream từng bước (suy nghĩ → tool → observation) + snapshot world cho animation |

### 8.4. Bộ kịch bản (33 file JSON trong `eval/scenarios/`)
- **Demo (live):** `warehouse_basic`, `warehouse_blocked`, `warehouse_dynamic`.
- **Eval v2 (m01–m11):** basic (m01–m03), obstacle (m04–m06), pick/drop (m07–m08), language (m09), infeasible (m10–m11).
- **Eval v1 (t01–t19):** bộ rộng hơn gồm replan, safety (người sát/đè đích/hai người), robustness (lệnh mơ hồ, bản đồ lớn), infeasible…

---

## 9. Đánh giá (Evaluation) — phương pháp & kết quả

### 9.1. Triết lý đánh giá: hai lớp TÁCH BẠCH (không bao giờ trộn)
Chạy bằng `python eval/run_eval_v2.py [--seeds N]`. Nguồn sự thật duy nhất: `eval/results/report_v2.md`.

- **Bảng B — Solver A\* xác định (KHÔNG phải agent):** giải tất định mọi task để **chứng minh môi trường giải được** và harness đúng. Không cần LLM, chạy ngay.
- **Bảng A — Agent thật (LLM, LangGraph):** chạy nhiều seed → báo **mean ± std + n**. Nếu chưa có backend LLM thì ghi rõ "CHƯA CHẠY", **không bịa số**.
- **Success luôn chấm bằng oracle độc lập** — không tin status agent tự khai.

### 9.2. Bộ chỉ số đánh giá agent (định nghĩa trong `SURVEY_metrics.md`)
- `success_rate` (trên task feasible) — mục tiêu ≥90%.
- `pass^k` (kiểu τ‑bench) — task đạt khi **thành công ở CẢ k seed** (đo độ tin cậy, không phải trung bình).
- **SPL** (Success weighted by Path Length) = `success × đường_tối_ưu / max(tối_ưu, thực_tế)` — đo hiệu quả đường đi so với lời giải A* tối ưu.
- `path_overhead` = đường thật / tối ưu, chỉ trên run thành công.
- `completion_rate` — % run kết thúc có kiểm soát (không timeout/exception).
- `valid_action_rate` — % bước gọi tool hợp lệ.
- `grounded_action_rate` — % hành động mutate (move/pick/drop) thực hiện **sau khi đã quan sát** (perceive/locate/check_path) — đo "tính có căn cứ".
- `infeasible/abstention accuracy` — % nhận diện đúng task bất khả thi (từ chối thay vì bịa).
- `hallucinated_done_rate` (honesty) — % run tự khai `done` nhưng oracle bác → mục tiêu 0%.
- `LLM calls/task`, `replans/task`, `latency/bước` — chi phí (báo nguyên trạng).

### 9.3. Kết quả Bảng B (xác định) — đã có, ổn định
- **9/9 task feasible thành công (success_rate = 100%)**, mỗi task ~4 bước (move→pick→move→drop).
- **infeasible_correct = 2/2** (m10 vật không tồn tại → `object_not_found`; m11 hàng bị bịt kín → `unreachable_object`).
- → Kết luận: **môi trường giải được và harness đúng**. (Lưu ý: Bảng B *không* phải năng lực agent.)

### 9.4. Kết quả Bảng A — Agent thật (Ollama `qwen2.5:7b` local, LangGraph)

- **n = 33** lần chạy (9 task feasible × 3 seed + 6 run infeasible). Success chấm bằng oracle độc lập.

| Chỉ số | Kết quả (mean ± std) | Mục tiêu | Nhận xét |
|---|---|---|---|
| **success_rate** (feasible) | **70.4% ± 33.1%** | ≥90% | Agent giải được 19/27 run feasible |
| **pass^k** (τ-bench, k=3) | **44.4%** | ≥80% | 4/9 task thành công ở cả 3 seed |
| **SPL** (path-efficiency) | **0.395 ± 0.438** | ≥0.80 | Agent đi vòng nhiều so với A* tối ưu |
| path_overhead (run thành công) | 4.86 ± 4.75 | ≤1.25 | Đường đi thật gấp ~5× tối ưu |
| **completion_rate** | **100.0%** (33/33) | 100% | ✅ Không timeout/exception nào |
| **valid_action_rate** | **98.6% ± 3.4%** | ≥95% | ✅ Gần như mọi bước đều là tool-call hợp lệ |
| grounded_action_rate | 40.1% ± 39.4% | ≥95% | Agent thường hành động mà chưa quan sát đủ |
| **infeasible/abstention** | **100.0%** (6/6) | 100% | ✅ Nhận đúng 100% task bất khả thi |
| **hallucinated_done_rate** | **0.0%** (0/33) | 0% | ✅ Không bao giờ khai khống hoàn thành |
| LLM calls/task | 30.2 ± 15.0 | (báo thật) | |
| replans/task | 0 | (báo thật) | Replan chưa được kích hoạt (core_scope=True) |
| latency/bước | 4.56s ± 0.56s | (báo thật) | Ollama 7B Q4_K_M, CPU+GPU |

**Phân tích theo category:**
- **basic** (m01–m03): success 100% (9/9 run) — agent giải tốt bài đơn giản.
- **pick/drop** (m07–m08): success 83.3% (5/6 run) — đa số đúng, 1 run thất bại.
- **language** (m09): success 66.7% (2/3 run) — xử lý tiếng Việt khá nhưng chưa ổn định.
- **obstacle** (m04–m06): success 33.3% (3/9 run) — điểm yếu rõ nhất: agent khó vượt tường/ngõ hẹp.
- **infeasible** (m10–m11): abstention 100% (6/6) — luôn từ chối đúng khi bất khả thi.

> **Nhận định trung thực:** Agent hoạt động end-to-end thật sự (không mock), đạt 70.4% success trên model 7B chạy local. Điểm mạnh: completion 100%, honesty 100% (không hallucinate done), valid_action 98.6%. Điểm cần cải thiện: SPL thấp (đi vòng), grounded_action_rate thấp, và obstacle category còn yếu. Với model mạnh hơn (Gemini cloud) hoặc prompt engineering tiếp, các chỉ số có thể cải thiện đáng kể.

---

## 10. Giao diện người dùng (Frontend)

- **Bản 2D** (`index.html` + `app.js`): nhập mục tiêu tiếng Việt, chọn kịch bản, xem canvas render robot/vật/người/vùng, bảng **kế hoạch** + **trace** cập nhật realtime qua WebSocket, panel "agent hỏi" khi cần xác nhận (human‑in‑loop), badge trạng thái.
- **Bản 3D** (`view3d.html` + `app3d.js`, dùng **Three.js**): scene editor — click ô lưới để đặt robot / pallet / vật cản / người / đích, rồi chạy agent trên cảnh tự dựng; dùng chung backend với bản 2D; hỗ trợ replay từ `frontend/replays/*.json`.
- Thương hiệu UI: **RoboPlanner** — "thế giới mô phỏng · agent thật"; có khối "Ứng dụng & Lộ trình tới robot thật".

---

## 11. Cách chạy (tóm tắt — chi tiết trong README.md)

```bash
# 1) Môi trường
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2) Cấu hình .env — chọn 1 trong 2 provider (KHÔNG dùng OpenAI)
#    A) Gemini:  LLM_PROVIDER=gemini  + GEMINI_API_KEY=...
#    B) Ollama:  LLM_PROVIDER=ollama  + OLLAMA_MODEL=qwen2.5:7b   (chạy: ollama pull qwen2.5:7b && ollama serve)

# 3) Chạy backend + UI
uvicorn src.main:app --reload --port 8000
#   UI: http://localhost:8000   |   API docs: http://localhost:8000/docs   |   health: /health

# 4) Test & eval
pytest
python eval/run_eval_v2.py            # Bảng B (không cần LLM)
python eval/run_eval_v2.py --seeds 3  # + Bảng A (cần Gemini hoặc Ollama)
```

---

## 12. Deliverables (trạng thái)
- [x] Source code (`src/`): World + 9 tool + LangGraph + LLM + UI 2D/3D + eval; invariants + oracle + cờ `core_scope` + bộ task move‑one‑object; bộ test mở rộng (sim/oracle/property/routing).
- [x] README.md, Architecture diagram (`docs/architecture_diagram.md`).
- [x] AI Logs (LangSmith) — đã cấu hình tracing.
- [x] Evaluation evidence (`eval/results/report_v2.md`) — Bảng B 100% + Bảng A agent thật: 70.4% success, 33 lượt, 3 seed.
- [x] Pitch deck, Weekly journal (`JOURNAL.md`), Worklog (`WORKLOG.md`).
- [ ] Live URL / Deploy (Render/Railway) — đã có config (`DEPLOY.md`), chờ bấm deploy.
- [ ] Video demo — kịch bản sẵn trong tài liệu kế hoạch.

---

## 13. Hạn chế & Hướng phát triển (Limitations & Roadmap)
**Hạn chế (trung thực):**
- Thế giới là **mô phỏng 2D**, chưa có robot/cảm biến thật; chưa có lớp an toàn cứng.
- Phạm vi đo v2 chỉ là **di chuyển 1 vật thể** với chướng ngại tĩnh.
- LLM local (Ollama 7B) chạy CPU → lần đầu nạp model chậm (~1–2 phút), latency/bước cao.
- Bảng A agent (70.4% success) chưa đạt mục tiêu ≥90%; obstacle category còn yếu (33.3%); SPL thấp (agent đi vòng).

**Hướng phát triển:**
- Bật lại (`core_scope=False`) các năng lực động: replan khi gặp người di chuyển, human‑in‑loop nâng cao, đa vật thể/đa robot.
- Cầu nối **sim → real**: nối tool `move/pick/drop` vào **ROS** + perception camera; thêm lớp an toàn cứng (LiDAR).
- Voice command; deploy live; mở rộng bộ eval và chạy đa seed/đa model (so sánh Gemini vs local).

---

## 14. Nhóm thực hiện (Team)
| Thành viên | Vai trò | MSSV |
|---|---|---|
| Lưu Công Thái | Agent core (LangGraph) + LLM · Product lead | 2A202600949 |
| Lê Hữu Đạt | Sim World + Tools + FastAPI/backend | 2A202600630 |
| Nguyễn Đình Tiến Mạnh | Frontend (canvas/trace) + Evaluation + Demo | _[điền MSSV]_ |

License: **MIT**.

---

## 15. Gợi ý bố cục SLIDE (cho Gemini dựng deck ~10–14 slide)
1. **Bìa:** RoboPlanner — Agent lập kế hoạch điều khiển robot kho bằng tiếng Việt (AI20K‑162 + 161). Tên nhóm.
2. **Vấn đề:** 3 nỗi đau (ngôn ngữ↔lập trình, môi trường động, hộp đen).
3. **Giải pháp + 3 feature:** ra lệnh tiếng Việt · plan & replan · minh bạch + human‑in‑loop.
4. **Định vị khác biệt:** "mô phỏng tất định + bất biến + oracle độc lập = kiểm chứng được, không hallucinate".
5. **Phạm vi v2 thu nhỏ (trung thực):** làm gì / cắt gì.
6. **Kiến trúc hệ thống:** sơ đồ tổng thể (FE ↔ FastAPI ↔ LangGraph ↔ LLM ↔ World ↔ LangSmith).
7. **Vòng lặp agent:** parse→perceive→plan→act→observe→(replan/ask/cap)→summarize.
8. **Lớp tool (9 primitive)** + nguyên tắc "tool đọc/ghi world thật, không bịa".
9. **Hai khoá kiểm chứng:** invariants (5 bất biến) + oracle (chấm độc lập, chống ảo tưởng done).
10. **Demo:** ảnh chụp UI 2D/3D + ví dụ lệnh "Đưa pallet A sang chuyền 3" và trace.
11. **Đánh giá — phương pháp:** Bảng A (agent) vs Bảng B (solver A*) tách bạch; bộ chỉ số (SPL, pass^k, honesty…).
12. **Kết quả:** Bảng B 9/9 feasible + 2/2 infeasible; Bảng A: 70.4% success, 44.4% pass^k, 100% honesty, 100% infeasible accuracy (n=33, 3 seed, Ollama 7B local).
13. **Hạn chế & Roadmap:** sim→real (ROS), năng lực động, deploy/video.
14. **Kết luận + lời cảm ơn.**

---

## 16. Thông điệp chốt (key takeaways để nhắc lại xuyên suốt)
- *"Robot là mô phỏng, nhưng agent là thật."* — LLM lập kế hoạch + gọi tool thật + đọc kết quả thật.
- *"Chúng tôi đo bằng oracle độc lập, không tin agent tự khai."* — chống ảo tưởng hoàn thành.
- *"Nhỏ nhưng đúng và chứng minh được."* — phạm vi thu nhỏ có chủ đích, mọi tuyên bố đều kiểm chứng được.
