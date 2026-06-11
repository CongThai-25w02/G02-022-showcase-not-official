# Prompt Phase 1 cho Claude Code — 9 tool thao tác World (AI20K‑162)

> Dán nguyên khối dưới đây vào Claude Code (đang mở repo App‑022).
> Bối cảnh: **Phase 0 đã xong** (World grid+A*, schemas, API `GET /world` + `POST /scenario`, frontend render; **27 test pass, ruff sạch**). Giờ làm **Phase 1**: hiện thực **9 tool** để agent thao tác `World`, mỗi tool có **pytest**. **CHƯA** wiring LangGraph/LLM (đó là Phase 2).

---

```
Đọc PLAN_agent_taskplanner.md (mục 7 + 12) và src/services/world.py, src/models/schemas.py.
Làm PHASE 1: 9 tool agent thao tác World + pytest. KHÔNG đụng LangGraph/LLM (để Phase 2).
Xong thì DỪNG để mình duyệt.

## Ràng buộc chung (bắt buộc)
- Python 3.12, type hints đầy đủ; `ruff check src tests` và `pytest -q` PHẢI xanh.
- CẤM HALLUCINATE: mọi tool đọc/ghi trạng thái THẬT trên World; output là quan sát thật.
- Mỗi tool là HÀM THUẦN, nhận `world: World`, trả về dict JSON-serializable
  (để Phase 2 khai báo function-calling). Không phụ thuộc LLM, không I/O mạng.
- Đặt trong src/agents/tools/ (vd tools.py + __init__.py export). XOÁ example_tool.py.
- Docstring mỗi tool = spec function-calling: mô tả ngắn + params (kiểu) + ý nghĩa output.
- Kiểm tra hợp lệ trước khi đổi state; sai thì trả {ok: False, error: "..."} chứ không raise.

## Bước A — mở rộng World (src/services/world.py)
Tách blocker tĩnh/động + thêm mutation (giữ API cũ không vỡ):
- is_blocked_static(cell): chỉ obstacle + ngoài biên (KHÔNG tính người).
  Giữ is_blocked() cũ (gồm người) cho perceive/check_path.
- astar_static(start, goal): A* chỉ tránh obstacle tĩnh.
  (Lý do: move_to tự đi rồi mới gặp người -> kích hoạt dừng/replan ở Phase 3,
   thay vì A* lặng lẽ vòng tránh người.)
- move_robot_to(target) -> dict: path = astar_static; ĐI TỪNG Ô; trước mỗi bước
  kiểm tra ô kế có NGƯỜI không -> nếu có thì DỪNG, trả
  {reached: False, blocked_by: <entity người>, pos: <pos hiện tại>};
  tới đích trả {reached: True, pos: target}. Cập nhật robot.pos thật.
  Không có path -> {reached: False, error: "no_path", pos: <pos hiện tại>}.
- pick_object(id_or_label) -> dict: chỉ khi robot cùng ô HOẶC kề vật và đang KHÔNG mang gì;
  set robot.carrying, đánh dấu vật đã được mang. Sai -> {ok: False, error}.
- drop_at(target) -> dict: chỉ khi đang mang; đặt vật xuống zone/ô đích; clear carrying.
- advance_tick(n=1): tăng state.tick.
- relative_position(cell) -> str: "trái/phải, gần/xa" so với robot (cho locate_object).

## Bước B — 9 tool (đúng PLAN mục 7), trong src/agents/tools/
Tri giác:
  1. perceive(world) -> {robot:{pos,carrying}, objects[], people[], obstacles[], zones[], tick}
  2. locate_object(world, label) -> {found, id?, pos?, zone?, relative?}
     -> SO KHỚP CHUẨN HOÁ (casefold + strip, bỏ dấu nếu được) để khớp nhãn TV ("pallet A").
  3. check_path(world, target) -> {clear: bool, blocker?: <entity>}  (người/vật cản trên đường?)
Hành động:
  4. move_to(world, target) -> world.move_robot_to(target)
  5. pick(world, object)    -> world.pick_object(object)
  6. drop(world, at)        -> world.drop_at(at)
Meta/an toàn:
  7. wait(world, ticks=1)        -> advance_tick + trả perceive mới
  8. ask_human(world, question)  -> {paused: True, question}   (không đổi world)
  9. done(world, summary)        -> {done: True, summary}

## Bước C — pytest (tests/test_tools/), mỗi tool >=1 happy + >=1 edge
Dùng kịch bản warehouse_basic / warehouse_blocked. Bắt buộc có các ca:
- move_to tới ô trong "chuyền 3" -> reached=True, pos đúng.
- move_to trong warehouse_blocked đụng người -> reached=False & blocked_by là person.
- pick khi CHƯA kề vật -> error; pick hợp lệ -> carrying được set.
- drop khi KHÔNG mang -> error; drop hợp lệ -> carrying = None.
- locate_object khớp cả "pallet A" và "PALLET a".
- check_path: 1 ca clear, 1 ca blocked.
- wait -> tick tăng.
- Giữ nguyên test Phase 0 (world + api) xanh.

## Khi xong
Liệt kê tool nào đã làm + test gì; dán kết quả `pytest -q` và `ruff check src tests`.
DỪNG, không tự nhảy sang Phase 2.
```

---

## Vì sao prompt này khác PLAN một chút (rút từ review Phase 0)

- **Tách `is_blocked_static` / `astar_static`:** hiện `is_blocked()` gộp luôn người, nên A* sẽ tự vòng tránh người. Nếu để vậy, kịch bản demo "người chắn lối → dừng/hỏi/replan" (Phase 3) sẽ khó kích hoạt. Cho `move_to` đi từng ô và dừng khi ô kế có người là cách giữ đúng vòng observe→replan.
- **So khớp nhãn chuẩn hoá ở `locate_object`:** `find_object()` đang khớp chính xác, mục tiêu tiếng Việt sẽ lệch hoa/thường/dấu → chuẩn hoá trước khi so.
- **`World` cần method mutation:** Phase 0 mới có hình học (đọc); Phase 1 là lúc thêm di chuyển robot, pick/drop (set `carrying`), tăng `tick` (cho `wait`).

## Hai việc KHÔNG thuộc Phase 1 nhưng nên nhớ
- **LLM provider:** `config.py` + `requirements.txt` đang là **OpenAI** (`openai_api_key`, `gpt-4o-mini`, `langchain-openai`) trong khi PLAN chọn **Gemini** (`langchain-google-genai`, `GEMINI_API_KEY`). Quyết trước **Phase 2**.
- **CORS:** `main.py` để `allow_origins=["*"]` + `allow_credentials=True` (trình duyệt sẽ bỏ qua) và bỏ qua `settings.cors_origins`. Sửa nhanh khi đụng tới deploy.
