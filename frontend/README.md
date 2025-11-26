# Wordle AI Visualizer

## Tính năng

### Bên Trái (Game Board)
- **Lưới 5x6**: Hiển thị các ô chữ giống game Wordle gốc
  - 🟩 Xanh lá: Chữ cái đúng vị trí
  - 🟨 Vàng: Chữ cái đúng nhưng sai vị trí
  - ⬜ Xám: Chữ cái không có trong từ

- **Bàn phím ảo**: Hiển thị trạng thái của các chữ cái đã đoán
  - Màu sắc thay đổi theo feedback
  - Layout QWERTY chuẩn

- **Chế độ chơi**:
  - **Auto Play**: AI tự động chơi (delay 2 giây/lượt)
  - **Hint Only**: Bấm "Next Step" để xem từng bước

### Bên Phải (Visualization & Brain)

#### 1. Khu vực Trie Structure
- Hiển thị các node đầu tiên (A-Z) của Trie
- **Active Path**: Con đường đang được thuật toán xét (màu đỏ)
- Node bình thường: màu xanh dương
- Cập nhật real-time khi AI đang suy nghĩ

#### 2. Khu vực Algorithm Info
- **Current Word**: Từ AI đang xét
- **Candidates**: Số lượng từ còn lại trong search space
- **Nodes Visited**: Số node đã duyệt trong lần search này
- **Entropy**: Thông tin entropy (cho các thuật toán cần)

#### 3. Log Panel
- Hiển thị 15 dòng log gần nhất
- Timestamp cho mỗi hành động
- Theo dõi:
  - "AI thinking..."
  - "AI guesses: CRANE"
  - "Feedback: 🟩🟨⬜⬜⬜"
  - "Pruning branch..."
  - "Calculating Entropy..."
  - Kết quả (thắng/thua)

## Cách sử dụng

### 1. Chạy trực tiếp
```bash
python frontend/visualize.py
```

### 2. Chọn chế độ
Khi chạy, chọn một trong các chế độ:
1. **DFS Solver - Auto Play**: DFS tự động chơi
2. **DFS Solver - Hint Only**: DFS từng bước
3. **Hill Climbing Solver - Auto Play**: Hill Climbing tự động
4. **Hill Climbing Solver - Hint Only**: Hill Climbing từng bước

### 3. Điều khiển trong game
- **Auto Play button**: Chuyển sang chế độ tự động
- **Hint Only button**: Chuyển sang chế độ manual
- **Next Step button**: Thực hiện một bước tiếp theo (chế độ Hint Only)
- **Close window**: Thoát

## Thuật toán được visualize

### DFS (Depth-First Search)
- Duyệt sâu vào Trie
- Tìm từ đầu tiên match với constraints
- Hiển thị path đi sâu vào một nhánh

### Hill Climbing
- Chọn chữ cái tại mỗi vị trí dựa trên frequency heuristic
- Greedy approach: chọn chữ phổ biến nhất
- Build từ từ trái sang phải

## Kiến trúc code

```
WordleVisualizer (main class)
├── GameBoard: Vẽ lưới 5x6
├── KeyboardVisualizer: Vẽ bàn phím
├── TrieVisualizer: Vẽ cấu trúc Trie
├── InfoPanel: Hiển thị thông tin thuật toán
├── LogPanel: Hiển thị execution logs
└── VisualizationLogger: Quản lý logs và stats
```

## Dependencies

- pygame >= 2.5.0

## Tùy chỉnh

### Thay đổi tốc độ Auto Play
Trong file `visualize.py`, dòng 490:
```python
auto_delay = 2.0  # seconds between auto moves
```

### Thay đổi số dòng log
Trong file `visualize.py`, dòng 36:
```python
def __init__(self, max_logs=15):  # Thay đổi số này
```

### Thay đổi màu sắc
Các constant màu ở đầu file (dòng 12-29):
```python
COLOR_BG = (18, 18, 19)
COLOR_TILE_GREEN = (83, 141, 78)
# ... etc
```

## Ghi chú kỹ thuật

- **60 FPS**: Smooth animation
- **Real-time updates**: Trie và info cập nhật ngay khi AI suy nghĩ
- **Responsive UI**: Buttons có hover effect
- **Log rotation**: Tự động xóa log cũ khi đầy

## Troubleshooting

### Pygame không cài được
```bash
pip install pygame --upgrade
```

### Game chạy chậm
- Giảm FPS: `self.clock.tick(30)` → `self.clock.tick(15)`
- Tắt bớt visualization

### Trie quá lớn không hiển thị hết
- Hiện tại chỉ show 26 chữ cái đầu tiên (A-Z)
- Active path sẽ show path đang xét
