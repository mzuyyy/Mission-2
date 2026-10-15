# Gamota Mission 2 · Nghiên cứu có căn cứ

Ứng dụng Python + Streamlit: câu hỏi/phạm vi → URL/PDF → evidence có locator →
nhận định fact/inference/hypothesis → phản chứng, thiếu dữ liệu → người dùng kiểm tra,
review và export JSON/Markdown.

**Giữ Gemini `gemini-2.5-flash-lite` theo chỉ dẫn mới nhất. Bản sửa PDF dùng layout,
giữ ngữ cảnh nguyên trang và prompt evidence-1.2. Hai ca nguồn thật từng sinh report
ở e1.1 nhưng PDF ghép sai số giữa các cột. Lượt live e1.2 đang BLOCKED HTTP 429;
chưa chứng minh model đã hết lỗi ngữ nghĩa sau sửa.**
Chưa đáp ứng toàn bộ [ACCEPTANCE](docs/ACCEPTANCE.md): semantic/completeness chưa được
người chấm độc lập xác nhận, chưa đo lợi ích tốc độ, chưa có video.
Repository đã public: [mzuyyy/Mission-2](https://github.com/mzuyyy/Mission-2).

## Bài nộp Mission 2

- [PowerPoint trình bày MVP](deliverables/Gamota_Mission_2_MVP_v2.pptx): 7 slide,
  ghi chú thuyết trình dự kiến **4 phút 40 giây**, gồm bài toán, luồng chứng minh,
  demo, ca khó và giới hạn. Đây là slide hỗ trợ quay, chưa phải video đã ghi hình.
- [Bộ tình huống kiểm thử](docs/SUBMISSION_TEST_CASES.md): 8 ca logic đã chạy,
  ca nguồn thật, failure PDF và lỗi quota; có Kỳ vọng → Thực tế → Đạt/Chưa đạt → Điều học được.
- [CI Linux đã đạt](https://github.com/mzuyyy/Mission-2/actions/runs/38711272415):
  67 test, Ruff, basedpyright, cài production từ lock và Streamlit health `ok`.
- Bản online: **https://mission2.streamlit.app/** (repo `mzuyyy/Mission-2`, nhánh `main`,
  entrypoint `app.py`, Python 3.12). Đã xác minh: API trạng thái của host trả
  `viewerAuthEnabled=false` (mở ẩn danh không cần đăng nhập); trình duyệt đã render
  đầy đủ tiêu đề "Gamota · Nghiên cứu có căn cứ · Streamlit" cùng form câu hỏi,
  nguồn và 4 tab Kết quả/Bằng chứng/Nguồn/Kiểm tra. Lưu ý thật: host free tier cho
  app ngủ khi không dùng, lần mở đầu có thể chờ wake; truy cập ẩn danh lần đầu đi
  qua 2–3 redirect handshake phiên của Streamlit rồi mới trả HTTP 200.
  [Hướng dẫn deploy](docs/DEPLOYMENT.md) và lệnh local bên dưới đã chuẩn bị;
  chạy offline được khi chưa có key hoặc Gemini hết quota.

## Chạy local

Môi trường đã thử: Windows, uv 0.11.19, Python 3.12.13. Yêu cầu Python 3.11–3.13 và uv.

```powershell
uv sync --frozen
uv run streamlit run app.py --server.address 127.0.0.1
```

Mở http://localhost:8501. Không cần API key để đọc URL/PDF, duyệt fixture hoặc replay.
Đã thử cài dependency production vào virtualenv sạch riêng với
`UV_PROJECT_ENVIRONMENT=runs/clean-env uv sync --frozen --no-dev` (Git Bash),
chạy CLI offline và khởi động Streamlit từ môi trường đó.

Cấu hình live bằng `.env` tại máy, dựa trên [.env.example](.env.example).
Không ghi đè `.env` có sẵn, không đưa key vào chat/Git:

```dotenv
LLM_API_BASE=https://api.openai.com/v1
LLM_MODEL=
LLM_API_KEY=
LLM_API_STYLE=openai_chat
LLM_JSON_MODE=true
LLM_TOKEN_PARAMETER=max_completion_tokens
```

Điền model mà tài khoản được phép dùng; base là URL API trước `/chat/completions`.
Adapter hiện hỗ trợ hợp đồng **OpenAI Chat Completions qua HTTPS**. Đổi endpoint/model
qua cấu hình; provider API khác cần adapter riêng. Nếu endpoint dùng `max_tokens`
hoặc không có JSON mode, cấu hình rõ sau khi kiểm tra tài liệu của endpoint đó.
Không tự đổi provider, model, tham số hoặc nới ngân sách khi lỗi.
Máy hiện tại dùng Google OpenAI-compatible endpoint với context 8.000 ký tự, output tối đa
2.500 token/request, tối đa 4 requests gồm retry. **2.500 là cap của app, không phải
giới hạn tối đa của Gemini.** `MAX_CONTEXT_CHARS` giới hạn phần nguồn gửi, khác với
`MAX_OUTPUT_TOKENS` giới hạn phần model sinh; RPM/TPM/quota là giới hạn dịch vụ riêng.
Context nhỏ hơn đã sinh report R02 nhưng không chứng minh nguyên nhân HTTP 503 là input lớn.
API đã đối chiếu [Chat Completions](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)
và [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=chat).

## Sử dụng

1. Nhập câu hỏi, một quốc gia/thị trường, nền tảng, kỳ đo hoặc để ngày unknown.
   Chọn tiêu chí, ghi ràng buộc và xác nhận phạm vi; không tự suy ra nghĩa “tiềm năng”.
2. Nhập URL mỗi dòng hoặc tải PDF có lớp chữ, bấm **Đọc URL/PDF**.
   Kiểm tra tab **Nguồn**; nguồn lỗi vẫn nằm trong coverage.
3. Metadata JSON tùy chọn theo ID `U1/U2` cho URL và `P1/P2` cho PDF.
   Hệ thống giữ provenance `user`; metadata tự khai chưa phải xác minh.
4. Khi cấu hình live đầy đủ và có quyền gửi nguồn tới dịch vụ đã cấu hình,
   bấm **Sinh nhận định từ nguồn**. Hai lượt chính: extraction rồi synthesis.
5. Mở **Mở bằng chứng C…** hoặc chọn claim ở tab **Bằng chứng**:
   xem quote nguyên văn, ngữ cảnh snapshot, nguồn, trang PDF và khoảng ký tự `[start,end)`.
6. Tab **Kiểm tra**: accept/needs_review/reject, ghi chú và sửa text.
   Lưu thành version mới, giữ trước/sau; sửa text hạ nhãn để chấm lại support.
7. Xuất JSON chứa nguồn/hash/history để replay; Markdown có anchor evidence ổn định.
   Replay luôn ghi thời điểm gốc. Không có câu trả lời mẫu tự động khi lỗi.

Ví dụ câu hỏi dùng cùng pipeline:

- So sánh tín hiệu nhu cầu puzzle và idle RPG tại Việt Nam trong Q2–Q3/2025.
- Dữ liệu danh mục nói gì về cạnh tranh mobile game tại Thái Lan, cần khảo sát thêm gì?
- Lượt tải tăng và doanh thu giảm có đủ kết luận một thể loại tăng trưởng tốt không?

Các câu này là ví dụ nhiệm vụ, không phải kết luận thị trường hoặc nhánh hardcode.
Fixture chỉ có dữ liệu giả lập. **Nạp fixture không sinh claims offline**.
Mock HTTP chỉ tồn tại trong tests; app/CLI không có chế độ trả đáp án mock.

Metadata mẫu:

```json
[{
  "source_id": "U1",
  "publisher": "Tên đơn vị ghi trên tài liệu",
  "source_kind": "company_disclosure",
  "country": ["VN"],
  "platforms": ["Android Google Play"],
  "data_period": "2025-Q2 to 2025-Q3",
  "methodology": "Mô tả phương pháp đã đọc; không đoán",
  "conflicts_of_interest": "Bên công bố có lợi ích thương mại",
  "original_root_id": "root_do_nguoi_doc_xac_nhan",
  "root_relation_reason": "Lý do và vị trí xác định nguồn gốc"
}]
```

Không biết trường nào thì bỏ trống trường đó. Ngày đăng không thay kỳ đo.
Nguồn chính thức không mặc định mạnh cho mọi claim; độc lập không suy từ domain.

## CLI và tái hiện

```powershell
uv run python -m gamota_research.cli fixtures --out runs/sources.json
uv run python -m gamota_research.cli inspect --request examples/request.json --sources runs/sources.json --out runs/selection.json
uv run python -m gamota_research.cli ingest --url "https://example.com" --out runs/public_sources.json
uv run python -m gamota_research.cli ingest --pdf report.pdf --out runs/pdf_sources.json
uv run python -m gamota_research.cli run --request examples/request.json --sources runs/sources.json --out runs/report.json
uv run python -m gamota_research.cli replay --bundle runs/report.json --out runs/replay.md
```

`run` cần cấu hình live thật; các lệnh còn lại dùng offline hoặc chỉ network tải nguồn.
`ingest` không truy cập nguồn nội bộ. Lệnh ghi output từ chối ghi đè để giữ artifact.
Chọn tên file mới khi chạy lại. `examples/request.json` dùng với fixture thì kết quả
luôn mang nhãn giả lập, kể cả gọi LLM thật.

## Kiểm thử và kết quả

```powershell
uv run pytest tests -q
uv run ruff check .
uv run ruff format --check .
uv run basedpyright
uv run playwright install chromium
uv run pytest tests/browser -m browser -q
uv run python eval/run_evaluation.py --split all --freeze-prompt
uv run python eval/run_evaluation.py --cases eval/real_cases.json --split real
```

Browser QA tự khởi động Streamlit mới rồi dừng server test, không dùng module cũ.
Mặc định pytest loại browser/live để không gọi dịch vụ tính phí hoặc cần browser.
Evaluator đóng băng input/kỳ vọng riêng, gọi CLI thật; expected không đi vào pipeline/LLM.
Reserved đã được evaluator đọc trong phiên triển khai; không gọi đây là benchmark chưa thấy trước.

Kết quả và lỗi thật ở [docs/TEST_RESULTS.md](docs/TEST_RESULTS.md).
Đã có 47 test offline PASS và browser flow PASS. Lượt trước: 10 ca fixture + 2 ca nguồn thật
BLOCKED do thiếu cấu hình. Lượt OpenRouter/Laguna mới nhất: hai ca nguồn thật BLOCKED HTTP 429.
Một lượt Laguna trước đó có R02 FAIL do quote không khớp span; pipeline đã từ chối kết quả.
Key từng được xác thực HTTP 200. Những lượt lịch sử này chưa sinh report, không tính PASS.
Các dòng OpenRouter trên là lịch sử. Lượt cuối Gemini: R01/R02 CLI exit 0; T03 fixture
gọi LLM thật exit 0; T01 HTTP 503, T04 HTTP 429. Quote checks lần lượt 5/5, 6/6, 3/3,
không phải tỷ lệ semantic support. Bản sửa PDF e1.2: offline **67 passed**,
browser regression **1 passed**; R01/R02 và một lượt thử lại riêng R02 BLOCKED HTTP 429.
Xem bảng mới nhất trong TEST_RESULTS; không coi báo cáo có citation hợp lệ là nghiên cứu đúng.
Không có tỷ lệ semantic support hoặc cải thiện tốc độ đã được chứng minh.

## Kiến trúc và giới hạn

Logic ở `src/gamota_research`, UI ở `app.py/ui_*.py`; cùng pipeline cho CLI.
Pydantic validate contracts; nguồn NFC/hash bất biến; retrieval lexical tiếng Việt,
có ưu tiên caveat và phân bố nguồn. Mọi span bỏ qua/nguồn bị cắt đều ghi coverage.
Quote/hash/IDs kiểm tra bằng code; hỗ trợ ngữ nghĩa và completeness cần người đọc.
Prompt `evidence-1.2` ưu tiên chọn span IDs; code trích nguyên văn span từ snapshot, giữ
xuống dòng/khoảng trắng và locator. Nhánh quote do model gửi vẫn phải khớp chính xác.
Trích evidence có chọn lọc; việc gửi một span không chứng minh đã đọc/chấm hết phản chứng.
PDF trích theo bố cục chữ, giữ khoảng trắng giữa cột và chữ xoay. Retrieval giữ một
trang snapshot trong một span; trang không vừa cap quote 6.000 ký tự hoặc ngân sách
context còn lại bị bỏ nguyên trang, ghi omitted IDs và warning. Cách này giảm recall
ở trang dài; cần tài liệu/bảng thay thế khi trang quyết định bị bỏ. Không nhận dạng chart
hoặc tự xác minh quan hệ số/nhãn; model phải để unknown nếu không rõ hàng/cột/kỳ đo.

Mặc định: 12 nguồn, 10 MiB/nguồn, 60 trang PDF, 60.000 ký tự snapshot/nguồn,
40.000 ký tự context (cấu hình hiện tại dùng 8.000), tối đa 4 request LLM/lượt
gồm retry/repair; mỗi stage tối đa 2 lần. HTML chia span khoảng 1.400 ký tự;
PDF giữ trang, cap quote 6.000 ký tự.
Giới hạn payload gồm metadata/evidence: context cap + 50.000 ký tự, ngoài schema hệ thống cố định.
Tokens/cost không biết giữ null. Chưa cấu hình bảng giá để tính tiền.
Giới hạn được validate trong config; không retry download.

URL: kiểm tra mọi DNS answer và redirect, kết nối numeric IP đã kiểm tra với Host/SNI gốc,
chặn private/loopback/link-local/reserved/multicast, credentials và port ngoài 80/443;
tắt proxy env, streaming cap bytes. Download/PDF chạy trong worker có deadline wall clock.
Chưa có hard memory sandbox cho PDF trên Windows.

Chỉ đọc HTML/text UTF-8 và PDF có lớp chữ. Không JS rendering, OCR, chart recognition,
nguồn khóa truy cập hoặc response nén. Trang chỉ có title báo chưa đọc được nội dung.
PDF bảng phức tạp có thể mất quan hệ ô, lexical retrieval có thể bỏ sót phản chứng.
Model có thể gán quote sai ý hoặc bỏ sót conflict: các check tự động không chứng minh semantic support.

Nguồn/thông tin riêng chỉ gửi khi người dùng có quyền và xác nhận.
Dữ liệu lưu theo session trong `runs/`, không cache raw report dùng chung.
Host tạm thời có thể mất file; tải JSON trước khi đóng phiên.
Không có tài khoản, quota toàn dịch vụ hoặc search web diện rộng.

## Chuẩn bị bàn giao

- `uv.lock` và `requirements.txt` pin đã chuẩn bị; `.streamlit/config.toml` giới hạn upload/theme.
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md): cấu hình deploy để chủ repo duyệt, chưa xuất bản.
- [STATUS.md](STATUS.md), [docs/DECISIONS.md](docs/DECISIONS.md): trạng thái và quan sát thật.
- [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md), [docs/DEMO.md](docs/DEMO.md), [docs/SUBMISSION.md](docs/SUBMISSION.md): checklist còn phải hoàn tất.

Code đã được đẩy và chuyển sang public theo yêu cầu người dùng tại
[mzuyyy/Mission-2](https://github.com/mzuyyy/Mission-2), nhánh `main`.
`.env`, backup key và dữ liệu chạy thử giữ local. Trạng thái deploy ghi ở đầu README;
chưa quay video.

