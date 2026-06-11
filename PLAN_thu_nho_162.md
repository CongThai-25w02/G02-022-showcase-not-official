# Kế hoạch thu nhỏ — RoboPlanner v2: "1 vật thể, simulation đúng"

| | |
|---|---|
| **Phiên bản** | 1.0 (draft) |
| **Ngày** | 2026‑06‑07 |
| **Theo** | Phản hồi mentor: *thu nhỏ phạm vi — agent di chuyển **1 vật thể** là đủ, nhưng **simulation phải hoàn thành đúng***. |
| **Liên quan** | `PRD.md` · `SPEC.md` · `eval/results/report.md` · (K:) `Dieu_chinh_du_an_AI20K162.md` |

> Tài liệu này chốt: (1) vì sao thu nhỏ, (2) phạm vi mới, (3) Giữ/Cắt/Hoãn, (4) **"simulation đúng" nghĩa là gì + cách chứng minh**, (5) eval trung thực, (6) việc cần làm, (7) Định nghĩa hoàn thành (DoD). Làm xong file này **trước khi** đụng code.

---

## 0. Vì sao thu nhỏ

Bản hiện tại trải quá rộng — 19 task / 8 nhóm, replan, người động, an toàn, voice, showcase, ablation — nhưng bằng chứng lại mỏng và có chỗ mâu thuẫn, đúng các điểm bị "bắt" trong review đầu tư: success **75% vs 100%**, **ablation chạy trên mock A\*** nhưng gắn nhãn "thật", **n=8** quá nhỏ, **"0 vi phạm an toàn"** chỉ do sim cấm cứng.

Mentor cắt đúng nút thắt: **làm ít hơn nhưng chắc**. Một task lõi — *agent di chuyển 1 vật thể* — với simulation đúng tới mức không bắt bẻ được. Lợi ích kép: phần bị cắt (người động, replan, safety) **chính là phần đẻ ra các claim đáng ngờ**, nên cắt đi là **giảm rủi ro uy tín**, không phải mất mát.

---

## 1. Phạm vi mới (north‑star, 1 câu)

> **Vận hành viên gõ 1 lệnh tiếng Việt → agent (LLM) tự lập kế hoạch và di chuyển ĐÚNG 1 vật thể tới đích trong một kho mô phỏng 2D có thẩm quyền, *xác định* và *kiểm chứng được*; mọi quan sát đọc từ trạng thái sim thật (không hallucinate).**

Task lõi **"move‑one‑object"**: `locate vật → đi tới → pick → đi tới đích → drop → done`, với chướng ngại **tĩnh** trên đường.

Giá trị bán hàng vẫn nguyên: NL → plan → tool‑calling đọc trạng thái thật → thực thi đúng. Đây **vẫn là vòng lặp agent thật**, không phải script — chỉ bỏ các nhánh phụ.

---

## 2. Giữ / Cắt / Hoãn

| | Nội dung |
|---|---|
| **GIỮ (lõi v2)** | • Vòng agent LangGraph rút gọn: `parse_goal → perceive → plan → act → observe → done` (+ `cap` an toàn)<br>• Tool đọc/ghi World thật: `perceive, locate_object, check_path, move_to, pick, drop, done`<br>• World sim 2D có thẩm quyền: grid, **`astar_static`** (tránh obstacle tĩnh), khớp tên tiếng Việt (`_normalize`)<br>• Eval harness + `report.md` (1 nguồn sự thật) + `pytest` + CI/`ruff`<br>• Minh bạch: plan + trace (node → tool(args) → observation → ✓/✗) + xuất audit log |
| **CẮT khỏi v2** *(gỡ khỏi code path lõi + khỏi mọi claim/headline)* | • Người **động** + nhánh **replan** (`astar` tránh người, `_dynamic`/`advance_tick`, `_route_replan`) → `tests/test_world/test_dynamic.py`, `tests/test_agents/test_replan_safety.py`<br>• `ask_human` / "an toàn" / `safety_events_handled` / "0 vi phạm"<br>• 19 task / 8 nhóm → còn **1 nhóm move‑one‑object** (nhiều biến thể)<br>• 3 scenario (basic/blocked/dynamic) → **1 world tĩnh** tham số hóa<br>• Nhập **giọng nói**, showcase nhiều chip, **ablation cũ** (đang chạy trên mock) |
| **HOÃN → Roadmap** *(không xóa, ẩn sau cờ/nhánh `legacy/`)* | • Replan khi gặp người động (giá trị thật, nhưng phải **đo đúng trên agent**)<br>• Human‑in‑loop / an toàn ngữ nghĩa<br>• Đa vật thể, đa robot, voice, perception bridge (sim→real), ROS |

> Nguyên tắc: phần **CẮT** vẫn có thể giữ trong nhánh/cờ tính năng, nhưng **không xuất hiện trong demo, số liệu, hay tài liệu v2**.

**Task eval giữ lại làm hạt giống** (đã có sẵn JSON): `t01_basic_move`, `t02_basic_drop`, `t03_obstacle_route`, `t04_obstacle_narrow`, `t05_pick_move_first`, `t07_language_case`, `t08_language_constraint`. Tùy chọn giữ `t16_infeasible_missing` để minh hoạ "agent biết nói không". **Bỏ/hoãn:** t06 (multi‑goal), t09–t14 (replan/safety), t17–t19.

---

## 3. "Simulation đúng" nghĩa là gì — DoD cho sim

Đây là **trọng tâm** mentor yêu cầu. "Đúng" = 6 thuộc tính, mỗi cái kèm cách chứng minh:

| # | Thuộc tính | Định nghĩa | Cách chứng minh |
|---|---|---|---|
| **S1** | **Tính xác định** | Cùng world khởi tạo + cùng chuỗi action → **cùng kết quả**, không phụ thuộc thời gian/thứ tự ngẫu nhiên | Chạy 2 lần, **hash chuỗi state phải trùng**; seed cố định; không để logic phụ thuộc thứ tự bất định của set/dict |
| **S2** | **Bất biến trạng thái** | Đúng sau **mọi** mutation: robot mang ≤1 vật; vật đang mang ở off‑grid `(-1,-1)`; mọi `pos` trong `[0,w)×[0,h)`; không thực thể nằm trên obstacle; vật đã drop nằm đúng ô | Hàm `assert_invariants(world)` gọi sau mỗi tool; **property‑based test** (Hypothesis) sinh chuỗi action hợp lệ |
| **S3** | **A\* đúng** | Đường liên tục 4‑hướng, không xuyên obstacle, độ dài tối ưu; báo `no_path` đúng khi bị bao | Unit test các ca: `start≡goal`, đường thẳng, vòng quanh obstacle, **bị bao kín**, ngoài lưới (mở rộng `test_world.py`) |
| **S4** | **pick/drop đúng luật** | `pick` chỉ khi Manhattan ≤1; `drop` đặt đúng ô đích hợp lệ; lỗi rõ ràng (`not_adjacent, already_carrying, not_carrying, object_not_found`) | Unit test **mỗi** nhánh ok + **mỗi** nhánh lỗi (mở rộng `test_tools.py`) |
| **S5** | **Observation = sự thật** | Mọi giá trị tool trả về khớp 100% World nội bộ (chống hallucinate) | Test bất biến hiện có — mở rộng cho **mọi** tool lõi |
| **S6** | **Không "đảm bảo giả"** | Không suy ra "an toàn/đúng" từ việc sim **cấm cứng**; chỉ đo cái thật xảy ra | Rà soát: bỏ mọi metric/claim kiểu "0 vi phạm do sim chặn"; ghi rõ **giả định mô hình** |

**Oracle độc lập cho task lõi:** một hàm kiểm tra **tách rời** `check_object_moved(world, object_label, dest) → bool`, trả `True` ⟺ vật ở đúng `dest` **và** robot không còn mang gì. Eval **so kết quả agent với oracle này** — không tin lời agent tự khai `done`.

---

## 4. Eval trung thực (v2)

- **1 nhóm task "move‑one‑object"**, ≥ **10–15 biến thể** (đổi vị trí vật/đích, bố cục obstacle tĩnh) → đủ n để có ý nghĩa.
- Mỗi task chạy **≥3 seed** (LLM ngẫu nhiên) → báo **mean ± std**, **luôn ghi n** và tổng số lần chạy (`run_multiseed.py` đã có sẵn).
- **1 nguồn sự thật duy nhất:** `eval/results/report.md` auto‑generate từ CSV. Công thức `success_rate = task done / task feasible`. README/slide trích **cùng bảng, cùng n** — không hai con số.
- **Tách 2 lớp rạch ròi, không trộn:**
  - Lớp **sim** (xác định): kiểm bằng test S1–S6, **không gọi LLM**.
  - Lớp **agent** (LLM): đo success/latency **mean ± std** trên seed thật.
  - Mock A\* (nếu dùng) chỉ để **kiểm môi trường**, **không bao giờ** gắn nhãn "agent thật".
- **Latency:** báo số thật (hiện ~4.44s/bước). Không cần đạt `<3s` ở v2 — nêu rõ *"đây là planner mức nhiệm vụ, không phải vòng điều khiển realtime"*.
- **Ablation:** **bỏ bản cũ** (chạy trên mock). Nếu muốn giữ: chạy đúng ON/OFF **trên agent LLM**, hoặc gắn nhãn *"harness A\* xác định — chưa chạy trên agent"* và **bỏ chữ "thật"**.

---

## 5. Việc cần làm (có thứ tự)

**P0 — Khóa sim (nền của mọi thứ)**
1. Viết `assert_invariants(world)` + cài vào sau mỗi tool (S2).
2. Property‑based test (Hypothesis) cho chuỗi action hợp lệ (S1, S2).
3. Test xác định bằng **hash state‑trace** (S1); bổ test A\* edge case (S3); pick/drop mọi nhánh (S4); mở rộng test observation (S5).
4. Viết oracle `check_object_moved()`.

**P1 — Rút gọn agent + eval**
5. Tỉa graph về `parse→perceive→plan→act→observe→done` (+`cap`); **ẩn** replan/`ask_human` sau cờ tính năng.
6. Sinh bộ task move‑one‑object (10–15 biến thể) từ các hạt giống ở §2 + chạy `run_multiseed.py` ≥3 seed.
7. `generate_report.py` xuất `report.md` mới (mean±std, n, 2 lớp tách bạch, dùng oracle).

**P2 — Dọn tài liệu/showcase cho khớp scope**
8. Cập nhật `PRD/SPEC/README` về scope v2; **gỡ** claim "0 vi phạm", "ablation thật", số mâu thuẫn.
9. Showcase tối giản: 1 demo move‑one‑object + replay + xuất audit log (bỏ voice/chip thừa).

---

## 6. Định nghĩa hoàn thành (DoD) — v2

- [ ] Mọi test **S1–S6 xanh**; sim chứng minh xác định (hash trùng qua 2 lần chạy).
- [ ] **Oracle độc lập** xác nhận agent thật sự di chuyển đúng vật (không tin lời tự khai).
- [ ] `report.md`: 1 bảng, có **n**, **mean±std** trên ≥3 seed, 1 nguồn sự thật, 2 lớp tách bạch.
- [ ] Không còn claim *"0 vi phạm an toàn"* / *"ablation thật"* sai nhãn ở bất kỳ tài liệu nào.
- [ ] `README/PRD/SPEC` mô tả đúng scope v2; phần CẮT chuyển sang Roadmap.
- [ ] Demo chạy được **offline** (replay) cho task move‑one‑object.

---

## 7. Roadmap (sau khi v2 chắc)

Replan (người động, **đo đúng trên agent**) → human‑in‑loop / an toàn ngữ nghĩa → đa vật thể & đa robot → voice → perception bridge từ ảnh thật (tái dùng OWL‑ViT) → ROS (sim→real).

---

## 8. Điểm mạnh cần GIỮ (đừng sửa mất)

Sự **trung thực trí tuệ** (tách "sim vs thật", "agent vs mock", có disclosure), bộ **test + CI + ruff**, **Pydantic schema**, và bản năng *agent đọc trạng thái thật thay vì tưởng tượng*. Thu nhỏ là để **bằng chứng xứng với chất lượng kỹ thuật**, không phải hạ thấp nó.
