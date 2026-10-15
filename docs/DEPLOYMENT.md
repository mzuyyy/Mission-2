# Triển khai Streamlit Community Cloud

Ứng dụng chạy local bằng `uv sync --frozen` và `uv run streamlit run app.py`.
`requirements.txt` đã export từ lock để host dùng pip nếu cần;
`pyproject.toml`/`uv.lock` vẫn là nguồn dependency chính.

Trạng thái 15/10/2026: repo đã public, Linux CI đã kiểm production startup.
App đã deploy tại **https://mission2.streamlit.app/** (`mzuyyy/Mission-2`, `main`,
`app.py`, Python 3.12). Đã xác minh từ máy này: DNS phân giải, trang chủ ẩn danh
trả HTTP 200 sau handshake phiên, API `/api/v2/app/status` trả
`viewerAuthEnabled=false` (không bắt viewer đăng nhập), và trình duyệt đã render
đầy đủ UI một lần khi container thức. Chưa ghi health `ok` từ `/_stcore/health`
vì lúc kiểm tra container đang ngủ/khởi động lại (trả vỏ SPA của host thay vì `ok`).
Không thay đổi setting nào trên host khi kiểm tra.

## Cách deploy đã chuẩn bị

1. Đăng nhập [Streamlit Community Cloud](https://share.streamlit.io), kết nối GitHub
   của chủ repo nếu được yêu cầu. Người dùng trực tiếp xử lý bước đăng nhập/2FA.
2. Chọn **Create app** → deploy từ GitHub. Repository `mzuyyy/Mission-2`, branch `main`,
   entrypoint `app.py`. Working directory là gốc repo.
3. Trong Advanced settings chọn Python **3.12**. Dependency có `uv.lock` và
   `requirements.txt`; project được cài editable để import được `gamota_research`.
4. Secrets: dùng nội dung [.streamlit/secrets.example.toml](../.streamlit/secrets.example.toml),
   điền key thật trực tiếp trong Secrets của host. Không thêm section `[llm]`:
   các khóa root-level được Streamlit đưa vào environment để `Settings()` đọc.
   Không commit `secrets.toml` hoặc gửi key qua chat.
5. Deploy rồi đợi build. Chỉ ghi URL sau khi host trả link thật và mở được app.
6. Kiểm tra: trang nhập câu hỏi; đọc một nguồn public; nguồn lỗi có warning;
   replay JSON mở đúng evidence; review tạo version; export tải được. Kiểm tra
   `/_stcore/health` từ URL public, không chỉ máy local/runner CI.
7. Thử một lần sinh live với Gemini nếu quota cho phép. Nếu 429 thì ghi BLOCKED,
   không gọi demo đọc nguồn/replay là nghiên cứu live AI thành công.

## Host và giới hạn
Python 3.12, working directory gốc repo, entrypoint `app.py`.
Streamlit bind theo cấu hình host; local chỉ bind 127.0.0.1.
Đặt LLM_API_BASE, LLM_MODEL, LLM_API_KEY và limits bằng biến môi trường server-side.
Không thêm key vào build args, image, repo, URL hoặc log. App đọc `.env` ở local;
host dùng environment hoặc cơ chế secrets của host đưa vào environment.
Root-level secrets đã đối chiếu tài liệu Streamlit; vẫn phải smoke test trên host thật.

## Những thứ đã chuẩn bị
- `.streamlit/config.toml`: upload 10 MB, giới hạn message, tắt telemetry, theme native.
- `uv.lock`, production `requirements.txt`, `.env.example` không secrets.
- Workspace ngẫu nhiên theo session; JSON/Markdown download để tránh mất file trên host ephemeral.
- URL pin IP/DNS/redirect, timeout worker, cap bytes/pages/context/request và lỗi không fallback.
- `eval/real_cases.json`: hai đầu vào nguồn công khai khác mục tiêu/phạm vi để thử sau cấu hình.
- `.github/workflows/ci.yml`: Linux offline checks và production startup, không có key.
  [Run đã đạt](https://github.com/mzuyyy/Mission-2/actions/runs/38711272415):
  67 passed, Ruff/type sạch, production health `ok`.

## Kiểm tra chất lượng và vận hành
Chạy live với model đã chọn, xác nhận API/token parameter/JSON mode và ngân sách thực tế.
Chấm tất cả material fact và completeness; test failure thật; không tính BLOCKED là PASS.
Public demo chỉ dùng nguồn công khai, quota host/chi phí tổng và quyền truy cập phải do host đặt:
MVP hiện mới có ngân sách per-run, chưa có quota toàn dịch vụ hoặc hệ tài khoản.
PDF parser có deadline nhưng chưa có hard memory sandbox Windows; dùng host giới hạn RAM/process.

Repo `https://github.com/mzuyyy/Mission-2`, nhánh `main`, đã public theo yêu cầu mới.
Đây là MVP public dùng nguồn công khai; không nhập tài liệu nhạy cảm. Mỗi run có cap
4 requests bao gồm retry; chưa có quota toàn dịch vụ/accounts. Quota provider không
đảm bảo độ sẵn sàng, không tự nâng cap, đổi model hoặc kích hoạt billing khi bị chặn.
Video chưa quay. Không có link demo online để báo thành công.

Tài liệu chính thức:
[Deploy](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app),
[Secrets](https://docs.streamlit.io/develop/concepts/connections/secrets-management).
