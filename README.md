# Agent Hub

Trang web tĩnh để học viên xem, tìm và mở nhanh các agent / command / skill / rule / reference
của **ba bộ**:

1. [AI-Agent-Master](https://github.com/fdhhhdjd/AI-Agent-Master)
2. [AI-Agent-Security-DevOps](https://github.com/fdhhhdjd/AI-Agent-Security-DevOps)
3. [MCP-STARTER-KIT](https://github.com/fdhhhdjd/MCP-STARTER-KIT) — bộ để tự xây MCP server

## Mở
Mở thẳng `agent-hub/index.html` bằng trình duyệt (không cần server). Cần mạng để tải font + icon
(Lucide) và hình nhân vật (DiceBear); mất mạng thì hình rơi về icon.

## Tính năng
- Lọc theo **bộ** (Master / Security & DevOps / Xây MCP riêng), theo **loại**, theo **chủ đề**, và ô tìm kiếm.
- Mỗi thẻ: hình nhân vật, tên, **mô tả đơn giản** (dùng để làm gì), nhãn loại + chủ đề.
- **Song ngữ VI/EN** — nút góc trên phải; mô tả đơn giản của bộ Master có cả 2 thứ tiếng.
- Bấm thẻ mở bảng chi tiết: dùng để làm gì, cách dùng (copy lệnh), mục lục, nội dung đầy đủ.
- **Không tải file** — mọi nút mở thẳng file gốc trên GitHub (nút ↗ trên thẻ, "Mở trên GitHub"
  trong bảng, và mỗi đường dẫn file đều là link). Chế độ sáng/tối.

## Cập nhật sau khi sửa nội dung 2 repo
```bash
python3 agent-hub/build.py
```
Sinh lại `data.js`. Mô tả thẻ lấy tự động từ chính file `.md`; riêng bộ Master có bản mô tả
đơn giản VI/EN viết tay trong `overrides.json`.

## Cấu trúc
| File | Vai trò |
|---|---|
| `index.html` | Giao diện (song ngữ, lọc, tìm, xem, link GitHub) |
| `build.py` | Quét 2 bộ → `data.js` (nhúng nội dung + link GitHub) |
| `overrides.json` | Mô tả "dùng để làm gì" đơn giản VI/EN cho bộ Master |
| `data.js` | Dữ liệu sinh tự động — không sửa tay |

> Đường dẫn 2 bộ ngoài đọc trong `build.py`: `SECOPS = ../AI-Agent-Devops`,
> `MCP = ~/Documents/LMS/mcp-starter-kit`. Nếu clone ở nơi khác, sửa 2 biến này.
