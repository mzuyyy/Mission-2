# Cấu hình bàn giao, chưa deploy

Ứng dụng chạy local bằng `uv sync --frozen` và `uv run streamlit run app.py`.
`requirements.txt` đã export từ lock để host dùng pip nếu cần;
`pyproject.toml`/`uv.lock` vẫn là nguồn dependency chính.

## Host dự kiến
Python 3.12, working directory gốc repo, entrypoint `app.py`.
Streamlit bind theo cấu hình host; local chỉ bind 127.0.0.1.
Đặt LLM_API_BASE, LLM_MODEL, LLM_API_KEY và limits bằng biến môi trường server-side.
Không thêm key vào build args, image, repo, URL hoặc log. App đọc `.env` ở local;
host dùng environment hoặc cơ chế secrets của host đưa vào environment.
Ví dụ root-level Streamlit secrets phải được chủ host xác nhận bằng smoke test khi deploy.

## Những thứ đã chuẩn bị
- `.streamlit/config.toml`: upload 10 MB, giới hạn message, tắt telemetry, theme native.
- `uv.lock`, production `requirements.txt`, `.env.example` không secrets.
- Workspace ngẫu nhiên theo session; JSON/Markdown download để tránh mất file trên host ephemeral.
- URL pin IP/DNS/redirect, timeout worker, cap bytes/pages/context/request và lỗi không fallback.
- `eval/real_cases.json`: hai đầu vào nguồn công khai khác mục tiêu/phạm vi để thử sau cấu hình.

## Điều kiện trước khi chủ repo yêu cầu publish
Chạy live với model đã chọn, xác nhận API/token parameter/JSON mode và ngân sách thực tế.
Chấm tất cả material fact và completeness; test failure thật; không tính BLOCKED là PASS.
Public demo chỉ dùng nguồn công khai, quota host/chi phí tổng và quyền truy cập phải do host đặt:
MVP hiện mới có ngân sách per-run, chưa có quota toàn dịch vụ hoặc hệ tài khoản.
PDF parser có deadline nhưng chưa có hard memory sandbox Windows; dùng host giới hạn RAM/process.

Repo ban đầu chưa có Git; chưa tạo remote, push public, deploy hoặc kiểm tra URL online.
Video chưa quay. Không có link demo online để báo thành công.
