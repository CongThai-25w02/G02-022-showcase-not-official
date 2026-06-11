# Prompt cho Claude Code — PHASE 0 (Sim World + render + API + test)

> Dán nguyên khối dưới đây vào Claude Code (mở trong repo `C2-App-022`).
> Phase 0 **chưa có LLM/agent** — chỉ dựng môi trường mô phỏng + giao diện render + API + test, làm nền cho các phase sau.

---

```
Bối cảnh: repo C2-App-022, đề tài AI20K-162 (agent lập kế hoạch tác vụ điều khiển robot kho
bằng ngôn ngữ tự nhiên, sim 2D). Đọc PLAN_agent_taskplanner.md và ARCHITECTURE.md trước.
Template là Python (FastAPI + LangGraph scaffold trong src/). PHASE NÀY CHỈ LÀM PHASE 0.

NHIỆM VỤ PHASE 0 — dựng World sim + render + API + test (KHÔNG đụng LLM, agent, tools):

1) src/models/schemas.py — Pydantic models:
   - Cell(x:int, y:int)
   - Entity(id:str, kind:Literal["robot","object","person","obstacle"], label:str|None,
            pos:Cell, carrying:str|None=None)
   - Zone(name:str, cells:list[Cell])               # vd "khu A", "chuyền 3", "lối thoát hiểm"
   - WorldState(width:int, height:int, robot:Entity, objects:list[Entity],
                people:list[Entity], obstacles:list[Entity], zones:list[Zone], tick:int)
   Có type hints đầy đủ; dùng được model_dump() để serialize JSON.

2) src/services/world.py — class World:
   - __init__(state: WorldState)
   - classmethod from_scenario(path|dict) -> World   # nạp bản đồ từ JSON
   - to_state() -> WorldState                        # trả trạng thái hiện tại
   - helper hình học: in_bounds(cell), is_blocked(cell) (người/obstacle/biên),
     neighbors(cell), astar(start, goal) -> list[Cell]|None   # BFS/A* tránh ô bị chặn
   - find_object(label) -> Entity|None ; zone_cells(name) -> list[Cell]
   (Phase 0 CHƯA cần move/pick — chỉ cần state + A* + truy vấn để phase sau dùng.)
   Không phụ thuộc LLM. Trạng thái giữ trong RAM.

3) Kịch bản mẫu — tạo thư mục eval/scenarios/ với 2-3 file JSON:
   - warehouse_basic.json (kho 16x10: robot, vài pallet/thùng có nhãn, zones khu A & chuyền 3,
     1-2 obstacle, 0 person) — task "đưa pallet A tới chuyền 3" khả thi.
   - warehouse_blocked.json (giống trên + 1 person chặn lối giữa → để test replan ở phase sau).
   Mỗi file đúng schema WorldState.

4) src/api/routes.py + src/main.py — FastAPI (giữ /health có sẵn):
   - GET /health -> {ok:true}
   - GET /api/v1/world -> WorldState hiện tại (JSON)
   - POST /api/v1/scenario {name} -> nạp eval/scenarios/<name>.json, trả WorldState
   - Phục vụ frontend tĩnh (StaticFiles mount "/").
   Gỡ/để trống phần agent example (chưa dùng); KHÔNG xoá services/llm.py, config.py.

5) frontend/ (index.html + app.js + style.css) — render bằng <canvas>:
   - fetch GET /api/v1/world → vẽ lưới 2D: robot (màu nổi), objects (kèm nhãn), people (đỏ),
     obstacles (xám), zones (vùng tô nhạt + tên).
   - 1 ô input "Mục tiêu" + nút "Chạy" (CHƯA nối backend — chỉ UI, để phase 2 nối).
   - dropdown chọn scenario (gọi POST /api/v1/scenario rồi vẽ lại).
   - Responsive + dark mode. Không framework nặng (vanilla JS là đủ).

6) tests/test_world/ — pytest:
   - nạp warehouse_basic.json → World.from_scenario ok, đúng số entity, robot đúng vị trí.
   - astar trả path hợp lệ (không đi qua ô bị chặn); trả None khi không có đường.
   - WorldState serialize/deserialize round-trip.

RÀNG BUỘC:
- Python type hints đầy đủ; pydantic; pytest xanh; `ruff check` sạch; không bare except.
- Không cần GEMINI_API_KEY ở phase này (chưa gọi LLM).
- Cập nhật requirements.txt nếu thêm dep (vd numpy nếu dùng — ưu tiên stdlib).

DoD PHASE 0 (tự kiểm trước khi báo xong):
- `uvicorn src.main:app --reload` chạy; GET /api/v1/world trả JSON đúng schema.
- Mở frontend → thấy kho 2D render đúng (robot + objects có nhãn + people + zones); đổi scenario được.
- `pytest -q` xanh; `ruff check src tests` sạch.

Làm xong Phase 0: liệt kê file đã tạo/sửa + kết quả pytest, rồi DỪNG để mình duyệt
(chưa sang Phase 1).
```

---

**Sau khi Claude Code xong Phase 0**, quay lại đây — mình sẽ soạn tiếp **prompt Phase 1** (9 tool thao tác World + pytest), rồi Phase 2 (LangGraph plan loop + Gemini). Cứ mỗi phase một prompt gọn để dễ kiểm soát chất lượng.
