# Kế hoạch Sensor — MÁY B (Gazebo) cho Agent AI20K‑162

> **File đôi với `PLAN_may_B_gazebo.md`.** File đó lo phần dựng tổng (ROS 2/Gazebo/Nav2/MoveIt/ARMBench). **File này chỉ trả lời 1 câu hỏi:** *robot mô phỏng cần gắn thêm sensor gì để agent chạy đủ vòng tool?*
>
> **Cách dùng cho Claude Code (máy B):**
> 1. Đọc **§2 (kết luận)** + **§3 (ma trận tool→sensor)** để hiểu *vì sao* cần.
> 2. Làm theo **§4 (checklist từng sensor)** — mỗi sensor có loại Gazebo, topic ROS, frame TF, và **DoD (lệnh verify)**.
> 3. Khi xong, **điền §6 (bảng báo cáo)** rồi tóm tắt lại — không cần viết lại file này.
>
> Quy ước trạng thái để báo cáo: `☐ chưa` · `◐ đang` · `✅ xong` · `⊘ N/A (bỏ)` · `⚠ blocked`.

---

## 0. TL;DR (1 dòng)

**Có — cần định nghĩa một bộ sensor tối thiểu trên robot** (repo hiện **chưa có** file `.sdf/.urdf/.xacro` nào, nên đây là thiết kế mới, không phải sửa). **3 BẮT BUỘC:** odometry, 2D LiDAR, RGB camera. **2 NÊN CÓ:** depth/RGB‑D, IMU. Còn lại optional hoặc không cần. **Không GPU → bỏ sensor render, dùng ground‑truth pose** (fallback đã ghi trong plan gốc).

---

## 1. Bối cảnh & ràng buộc

- Agent dùng chung interface `WorldBackend`; `GazeboBackend` map tool → ROS 2 (xem `PLAN_may_B_gazebo.md` §4). **Không sửa lớp agent** — chỉ thêm nguồn dữ liệu (sensor) để các tool có thật để đọc.
- **Hiện trạng repo:** quét toàn bộ → **0 file robot description** (`.sdf/.urdf/.xacro/.world`) và **0 node ROS** được commit. Phần "máy B giai đoạn 1 ✅" nằm trên PC Linux riêng, chưa vào repo này. ⇒ Bộ sensor dưới đây là **spec để dựng**, không phải kiểm kê cái đã có.
- **Nguyên tắc chống phình (deadline >1 tuần):** chỉ thêm sensor nào có **một tool hoặc một đường perception thật** tiêu thụ. Mỗi sensor phải truy ngược được về một dòng trong §3.

---

## 2. Kết luận — agent cần thêm sensor gì?

| Mức | Sensor | Vì sao (gắn với tool agent) |
|---|---|---|
| **BẮT BUỘC** | **Wheel odometry** (từ plugin diff‑drive/ackermann) | `move_to`, `perceive` — Nav2 cần `odom→base_link` để định vị & đi. Không có thì không di chuyển được. |
| **BẮT BUỘC** | **2D LiDAR** | `move_to`, `check_path` — Nav2 localize (AMCL/SLAM) + lớp obstacle của costmap; cũng là nguồn phát hiện **người/vật cản động** → kích hoạt replan/an toàn (giống bản 2D). |
| **BẮT BUỘC** | **RGB camera** (trước robot) | `locate_object` — đầu vào cho **ARMBench detector** nhận diện pallet/thùng; cũng là hình cho `perceive`/Foxglove. |
| **NÊN CÓ** | **Depth / RGB‑D camera** | `locate_object` — biến bbox 2D → **pose 3D** để pick chính xác. Thiếu thì chiếu xuống mặt sàn hoặc dùng ground‑truth pose. |
| **NÊN CÓ** | **IMU** | `move_to` — fuse với odom (robot_localization EKF) cho định vị mượt, đỡ trượt bánh. Rẻ, không cần GPU. |
| **OPTIONAL** | **Fork joint state** (`/joint_states`) | `pick`/`drop` — biết chiều cao càng nâng. *Lưu ý:* đây là output của khớp/JointStatePublisher, **không phải "sensor" gắn thêm**; chỉ cần nếu chọn model **xe nâng có khớp fork**. Nếu chọn **AMR kéo** → ⊘ N/A. |
| **OPTIONAL** | **Force/Torque** (đầu càng) | `pick` — xác nhận đã nâng được pallet. Fallback: attach + đọc ground‑truth model pose. |
| **OPTIONAL** | **Contact / bumper** | An toàn va chạm / xác nhận chạm pallet. Fallback: ground‑truth. |
| **KHÔNG CẦN** | GPS/navsat, 3D LiDAR, đa camera/360, magnetometer, air‑pressure, segmentation/bbox‑camera | Kho trong nhà + map tĩnh + 1 task demo → thừa. Đừng thêm (ngốn GPU + thời gian, không tool nào dùng). |

> **Người (safety):** **không cần sensor riêng.** Người xuất hiện như **vật cản động trong costmap LiDAR** → Nav2 trả `blocked_by` → đúng vòng `wait`/`ask_human`/replan như bản 2D. Camera person‑detector chỉ là stretch; ground‑truth pose người là fallback luôn chạy.

---

## 3. Ma trận Tool → Sensor → Fallback (truy nguồn "vì sao cần")

| Tool agent | Hiện thực ROS 2 | Sensor tiêu thụ | Mức | Fallback nếu thiếu sensor |
|---|---|---|---|---|
| `perceive` | đọc `/tf` `/odom` `/scan` `/camera` | odom, lidar, camera | — | đọc ground‑truth state từ `gz` |
| `locate_object` | ARMBench detector trên ảnh | **RGB camera** (+depth cho 3D) | bắt buộc/nên | **ground‑truth model pose** (ghi disclosure) |
| `check_path` | Nav2 `ComputePathToPose` | **LiDAR** (+map) | bắt buộc | map tĩnh + costmap rỗng (kém thực) |
| `move_to` | Nav2 `NavigateToPose` | **LiDAR + odom** (+imu) | bắt buộc | ground‑truth pose teleport (không "thật") |
| `pick` | MoveIt + khớp fork | `/joint_states` (+F/T) | optional | attach + ground‑truth, bỏ F/T |
| `drop` | MoveIt hạ + nhả | `/joint_states` | optional | như trên |
| `wait`/`ask_human` | logic agent | (người = vật cản LiDAR) | — | ground‑truth pose người |
| `done` | logic agent | — | — | — |
| **oracle** | đọc ground‑truth `gz model state` | **không phải sensor on‑board** | — | — (luôn dùng ground‑truth, không tin `done`) |

---

## 4. Checklist sensor (làm theo + có DoD để báo cáo)

> Mỗi mục: gắn vào URDF/SDF robot, bật bridge `ros_gz_bridge`, rồi chạy lệnh **DoD** để xác nhận topic ra ROS. `[type]` = tên sensor trong Gazebo Harmonic (gz‑sim 8).

### ☐ S1 — Wheel odometry · **BẮT BUỘC** · không cần GPU
- **Phục vụ:** `move_to`, `perceive`, toàn bộ Nav2.
- **Nguồn:** plugin truyền động `DiffDrive` / `AckermannSteering` (không phải khối `<sensor>`).
- **Topic ROS:** `/odom` → `nav_msgs/msg/Odometry` · **TF:** `odom → base_link`.
- **DoD:** `ros2 topic hz /odom` ra ~tần số ổn định; `ros2 run tf2_ros tf2_echo odom base_link` đổi khi robot chạy.

### ☐ S2 — 2D LiDAR · **BẮT BUỘC** · cần render (GPU hoặc software chậm)
- **Phục vụ:** `move_to`, `check_path`, phát hiện người/vật cản.
- **Loại gz:** `[gpu_lidar]` (1 tầng, quét ngang).
- **Topic ROS:** `/scan` → `sensor_msgs/msg/LaserScan` · **TF:** `base_link → laser_frame`.
- **DoD:** `ros2 topic echo /scan --once` có mảng `ranges`; thấy quét trong RViz2/Foxglove; Nav2 costmap hiện vật cản.

### ☐ S3 — RGB camera (trước) · **BẮT BUỘC** · cần render
- **Phục vụ:** `locate_object` (ARMBench), hình cho `perceive`/Foxglove.
- **Loại gz:** `[camera]`.
- **Topic ROS:** `/camera/image` → `sensor_msgs/msg/Image` (+ `/camera/camera_info` → `sensor_msgs/msg/CameraInfo`) · **TF:** `base_link → camera_link`.
- **DoD:** xem được ảnh trong Foxglove/`rqt_image_view`; ARMBench node nhận được frame.

### ☐ S4 — Depth / RGB‑D · **NÊN CÓ** · cần render (nặng hơn)
- **Phục vụ:** `locate_object` → pose **3D** của pallet để pick.
- **Loại gz:** `[rgbd_camera]` (hoặc `[depth_camera]`).
- **Topic ROS:** `/camera/depth/image` → `sensor_msgs/msg/Image`; `/camera/points` → `sensor_msgs/msg/PointCloud2`.
- **DoD:** point cloud hiện trong RViz2; tra được khoảng cách tới pallet.
- **Bỏ khi:** không GPU → chiếu detection xuống mặt sàn **hoặc** ground‑truth pose (ghi disclosure).

### ☐ S5 — IMU · **NÊN CÓ** · không cần GPU
- **Phục vụ:** `move_to` — fuse odom+imu (robot_localization EKF) cho định vị ổn định.
- **Loại gz:** `[imu]`.
- **Topic ROS:** `/imu` → `sensor_msgs/msg/Imu` · **TF:** `base_link → imu_link`.
- **DoD:** `ros2 topic echo /imu --once` có orientation/angular_velocity hợp lý.

### ☐ S6 — Fork joint state · **OPTIONAL (chỉ nếu xe nâng có khớp fork)** · không cần GPU
- **Phục vụ:** `pick`/`drop` — biết chiều cao càng.
- **Nguồn:** khớp prismatic của fork + `JointStatePublisher` (không phải `<sensor>`).
- **Topic ROS:** `/joint_states` → `sensor_msgs/msg/JointState`.
- **DoD:** `ros2 topic echo /joint_states --once` thấy khớp fork; giá trị đổi khi nâng/hạ.
- **⊘ N/A khi:** chọn model **AMR kéo** (không có khớp nâng) — ghi rõ trong báo cáo.

### ☐ S7 — Force/Torque đầu càng · **OPTIONAL** · không cần GPU
- **Phục vụ:** `pick` — xác nhận đã nâng được pallet (đo tải).
- **Loại gz:** `[force_torque]`.
- **Topic ROS:** `/fork/ft` → `geometry_msgs/msg/WrenchStamped`.
- **DoD:** lực đổi rõ khi mang vs không mang pallet.
- **Fallback:** dùng attach + so ground‑truth model pose → bỏ luôn S7.

### ☐ S8 — Contact / bumper · **OPTIONAL** · không cần GPU
- **Phục vụ:** xác nhận chạm pallet / an toàn va chạm.
- **Loại gz:** `[contact]`.
- **Topic ROS:** `/bumper` → `ros_gz_interfaces/msg/Contacts`.
- **DoD:** sự kiện contact bật khi chạm; fallback ground‑truth nếu bỏ.

---

## 5. GPU / headless — quyết định nhánh

Tách theo **chi phí render**, để chạy được cả khi máy B không có GPU:

- **Sensor physics‑only (luôn chạy, không GPU):** S1 odom, S5 IMU, S6 joint_states, S7 F/T, S8 contact. ⇒ đủ cho một vòng nav+manip "mù", perception bằng **ground‑truth pose**.
- **Sensor render (cần GPU, hoặc software rất chậm):** S2 LiDAR, S3 camera, S4 depth.

| Nhánh | Khi nào | Bật sensor nào |
|---|---|---|
| **A — có GPU** | máy B có card | Full: S1–S5 (+S6 nếu xe nâng). Đây là bản "perception thật" để showcase. |
| **B — không GPU / headless** | máy B yếu / ngày demo GPU bận | Chỉ physics‑only (S1, S5, +S6); `locate_object` & `perceive` dùng **ground‑truth pose**; LiDAR tắt hoặc hạ tần số. **Ghi disclosure rõ.** |

> Khớp với `PLAN_may_B_gazebo.md` §7 ("Không GPU → Gazebo headless, giảm sensor, ưu tiên fallback").

---

## 6. Bảng báo cáo cho Claude Code (điền khi làm)

> Sau khi dựng, chạy `ros2 topic list` + các lệnh DoD ở §4 rồi điền bảng này và báo lại.

| Sensor | Trạng thái | Topic thấy trong `ros2 topic list`? | Tool/Nav2 dùng OK? | Ghi chú (frame, tần số, fallback) |
|---|---|---|---|---|
| S1 Odometry | ☐ | `/odom` ☐ | | |
| S2 2D LiDAR | ☐ | `/scan` ☐ | | |
| S3 RGB camera | ☐ | `/camera/image` ☐ | | |
| S4 Depth/RGB‑D | ☐ | `/camera/points` ☐ | | |
| S5 IMU | ☐ | `/imu` ☐ | | |
| S6 Fork joint | ☐ / ⊘ | `/joint_states` ☐ | | (⊘ nếu chọn AMR kéo) |
| S7 Force/Torque | ☐ / ⊘ | `/fork/ft` ☐ | | |
| S8 Contact | ☐ / ⊘ | `/bumper` ☐ | | |

**Lệnh verify nhanh (chạy 1 lượt):**

```bash
ros2 topic list                       # liệt kê topic — đối chiếu cột giữa
ros2 run tf2_tools view_frames        # xuất cây TF (odom→base_link→các sensor frame)
ros2 topic hz /odom                   # odom có chạy?
ros2 topic echo /scan --once          # lidar có ranges?
ros2 topic echo /imu --once           # imu có dữ liệu?
ros2 topic echo /joint_states --once  # khớp fork (nếu có)
# Camera/depth: mở Foxglove (foxglove_bridge :8765) hoặc rqt_image_view
```

**Mẫu câu báo cáo:** *"Bộ sensor máy B: S1/S2/S3 ✅ (topic + Nav2 đi tới điểm OK), S4 ◐ (depth có cloud, chưa nối locate_object), S5 ✅, S6 ⊘ (dùng AMR kéo), S7/S8 bỏ. Nhánh A (có GPU). locate_object đang dùng ARMBench detector / ground‑truth: …"*

---

## 7. Định nghĩa hoàn thành (DoD bộ sensor)

- [ ] Nav2 đưa robot **tới điểm chỉ định** dùng **`/scan` + `/odom`** (không teleport bằng ground‑truth cho việc đi).
- [ ] `locate_object` trả **pose pallet** từ camera (ARMBench) **hoặc** ghi rõ đang dùng ground‑truth fallback.
- [ ] (Nếu xe nâng) `pick`/`drop` đọc được chiều cao càng từ `/joint_states`.
- [ ] Cây TF liền mạch `map → odom → base_link → {laser, camera, imu}` (`view_frames`).
- [ ] **Không có sensor nào ngoài danh sách §2** (chống phình).
- [ ] Ghi **disclosure** mỗi chỗ dùng ground‑truth thay sensor thật (đồng bộ với §8 plan gốc).

---

## 8. Việc cần chốt (liên kết `PLAN_may_B_gazebo.md` §9)

- **Model robot:** xe nâng có **khớp fork** (cần S6, có thể S7) hay **AMR kéo** (bỏ S6/S7, đơn giản hơn cho deadline)? → quyết trước khi dựng.
- **GPU máy B:** có → nhánh A (bật S2–S4 perception thật); không → nhánh B (physics‑only + ground‑truth).
- **`locate_object`:** ARMBench detector thật hay ground‑truth pose cho bản nộp? → ghi disclosure tương ứng.
