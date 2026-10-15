# Kết quả kiểm thử thực tế

## Kết quả hiện tại: giữ Gemini, prompt evidence-1.1

15/10/2026, khoảng 14:00–14:07 GMT+7. Google OpenAI-compatible endpoint,
`gemini-2.5-flash-lite`, context 8.000 ký tự, output 2.500 token/request, tối đa 4 requests.
Cap 2.500 do app đặt, không phải giới hạn tối đa Gemini. Không tăng cap hoặc thay cấu hình billing; chi phí thực tế vẫn unknown.
Nguồn được parse đầy đủ vào snapshot; retrieval có thể chỉ gửi một phần và ghi omission.

| Ca | Kỳ vọng | Kết quả thực tế | Đánh giá | Điều học được |
| --- | --- | --- | --- | --- |
| R01 VNG HTML | Tách dữ liệu công ty với nhu cầu game VN | CLI exit 0,5 claims,5 evidence,4 requests; quote 5/5 | Chạy được; human semantic review NOT_RUN | Nhận định thiếu dữ liệu có premise; recommendations blocked |
| R02 Sea PDF | Phạm vi Garena/Thái Lan và chỉ số đúng | CLI exit 0,5 claims,6 evidence,3 requests; quote 6/6 | Chạy được; agent audit phát hiện lỗi số liệu, chưa đạt chất lượng | Model ghép số khác cột/kỳ dù quote có thật; không tính PASS |
| T01 fixture good | So sánh hai thể loại có caveat | CLI exit 2,HTTP503,2 requests | BLOCKED | Chưa có report để chấm, không phải model-quality FAIL |
| T03 fixture ambiguous | Không đồng nhất lượt tải với doanh thu | CLI exit 0,3 evidence,3 requests; quote 3/3 | Chạy được; human semantic review NOT_RUN | Input synthetic, gọi model thật; không coi là nghiên cứu thị trường thật |
| T04 fixture conflict | Hiện mâu thuẫn và chặn recommendation | CLI exit 2,HTTP429,3 requests | BLOCKED | Chưa chứng minh phát hiện conflict live từ lượt này |

Lệnh đã chạy:
- `uv run python eval/run_evaluation.py --cases eval/real_cases.json --split real --freeze-prompt`
  lúc context 40.000 ký tự: R01CLI exit 0, R02HTTP503; artifacts `6b663267075b4fcb9e4ef1454bb4eca6`.
- Chạy riêng R02 context 8.000 ký tự sau một lượt503 nữa: CLI exit 0; báo cáo ở
  `eval/runs/gemini_output_fix/r02_context_8000/`. Không gán việc giảm context là nguyên nhân
  đã chứng minh của việc hết503; T01 sau đó vẫn503.
- Persist context 8.000 ký tự, giữ model/key: `uv run python eval/run_evaluation.py --cases
  eval/real_cases.json --split real` → R01/R02CLI exit 0, artifacts
  `eval/runs/fa5bafbbe8004b5b8509274e1a56d59e/`.
- `uv run python eval/run_evaluation.py --cases eval/smoke_cases.json --split dev` →
  T01/T04BLOCKED, T03CLI exit 0; `eval/runs/7acbfef913af497b997b72426a83a378/`.
  `eval/smoke_cases.json` chỉ chọn ba dev case đã có; không thêm expected vào pipeline.
- `uv run pytest tests -q --junitxml=eval/runs/gemini_output_fix/offline_after.xml`
  →62 passed,1 deselected,10.66s; mock/fixture logic.
- `uv run pytest tests/browser -m browser -q --junitxml=eval/runs/gemini_output_fix/browser_after.xml`
  →1 passed,11.41s; synthetic replay, không gọi LLM.
- `uv run ruff check .`, `uv run basedpyright`: sạch sau sửa; format check sạch.

Ba report có quote hợp lệ không tương đương ba ca chất lượng PASS. Raw evaluator vẫn
BLOCKED chờ người chấm. Tỷ lệ support do người chấm, unsupported count và missed conflicts
vẫn unknown/NOT_RUN; lỗi agent đối chiếu ghi riêng trong `agent_review.json` của R02.
Chưa đo baseline/tốc độ người dùng, chưa đủ ≥5 report live được chấm đạt, chưa deploy.

Các mục dưới là lịch sử tại từng thời điểm, không phải cấu hình/trạng thái hiện tại.

## Chạy lại với cấu hình Laguna do người dùng thay đổi

Ngày 15/10/2026, khoảng 11:58 GMT+7. Không có evaluator Windows/WSL đang chạy khi
kiểm tra; giữ nguyên các artifact đã có và `.env` người dùng. Model hiện tại
`poolside/laguna-s-2.1:free`, timeout 45 giây, tối đa 4 request gồm retry/repair.

Lệnh đã chạy: `uv run python eval/run_evaluation.py --cases eval/real_cases.json --split real`.
Evaluator exit 0, nhưng hai production CLI đều exit 2: evaluator hoàn tất việc ghi kết quả,
không phải chất lượng PASS. Không mock/fallback, không tăng ngân sách, không đổi model.

| Ca | Kỳ vọng | Kết quả thực tế | Verdict | Điều học được |
| --- | --- | --- | --- | --- |
| R01 VNG HTML | Report phân biệt dữ liệu công ty với nhu cầu riêng VN | Đọc được nguồn, provider HTTP 429, không report | BLOCKED | Chưa kiểm tra được nội dung nhận định |
| R02 Sea PDF | Report phân biệt Garena toàn cầu với cạnh tranh riêng TH | Đọc được nguồn, provider HTTP 429, không report | BLOCKED | Chưa thể kiểm tra lại lỗi citation của lượt trước |

Artifact mới: `eval/runs/64a2c5b70eef48b28a0d17c79a5de846/`, gồm request, source/hash,
retrieval, kỳ vọng evaluator riêng, cli.log/result.json. Usage/request_count khi lỗi vẫn null.
Chưa có metadata để xác định upstream cụ thể của lỗi 429 Laguna; không dùng chẩn đoán
Google AI Studio của model Gemma trước đó làm kết luận cho model mới.

Artifacts có sẵn được quan sát trước lượt chạy mới:

- `e68dc038dec145e6827ca47c7a64b59f`: R01 BLOCKED HTTP 429; R02 **FAIL**
  `citation: E1: quote không khớp span đã chọn.` Model ghi nhận là Laguna.
  Đây là failure live extraction/locator, không phải failure bị tạo từ mock. Code từ chối report;
  chưa có raw extraction để xác định chính xác quote sai ở ký tự nào hoặc nguyên nhân model.
- `8254ffb25a1b4221b0a967ac9d5773d6`: R01 BLOCKED timeout, R02 không có result,
  không có results.json tổng. Lượt chưa hoàn tất, không tự gán kết quả cho R02.

Phiên này không đổi source code, không chạy lại offline/browser suite. Các kết quả PASS bên
dưới thuộc lượt trước. Bước tiếp theo là chạy khi provider khả dụng, lưu extraction lỗi
với kiểm soát dữ liệu và kiểm tra nguyên nhân citation; giữ yêu cầu quote khớp nguyên văn.

## Lượt OpenRouter sau khi người dùng điền key

Ngày 15/10/2026, khoảng 11:43–11:45 GMT+7. Giữ nguyên cấu hình người dùng:
`https://openrouter.ai/api/v1`, `google/gemma-4-31b-it:free`, JSON mode,
tối đa 4 request/lượt gồm retry. Không đổi provider/model hoặc tăng giới hạn.

- Lệnh thật: `uv run python eval/run_evaluation.py --cases eval/real_cases.json --split real`.
- R01 (VNG HTML) và R02 (Sea PDF): nguồn đọc được, CLI exit 2,
  `provider_retryable: Provider trả HTTP 429; không đổi model/provider.`; **2 BLOCKED**.
- Đã thử API live, không mock. Không sinh được report; locator/semantic/completeness chưa chấm.
  `request_count` trong evaluator giữ null khi lỗi vì CLI chưa xuất usage, không ghi nhầm thành 0.
- Chẩn đoán riêng: GET `/api/v1/key` HTTP 200; một POST completion nhỏ HTTP 429,
  provider `Google AI Studio`, thông báo `temporarily rate-limited upstream`.
  Đây là lỗi upstream được quan sát, không phải lỗi xác thực hoặc bằng chứng chất lượng model.
  Không suy số request miễn phí còn lại từ usage tiền hoặc trường rate_limit deprecated.
- Artifact: `eval/runs/4649b693afb8403fad753b7a532f0b31/`: input/hash/retrieval,
  expected tách riêng, cli.log/result.json cho từng ca và diagnostic.json đã loại secrets.
- Regression: `uv run pytest tests -q --junitxml=eval/runs/openrouter_offline_regression.xml`:
  **47 passed, 1 deselected, 6.47s**. Offline/mock, không phải live research PASS.

Theo [OpenRouter limits](https://openrouter.ai/docs/api_reference/limits), HTTP 429 thuộc
giới hạn request; phản hồi upstream cụ thể được lưu trong artifact. Tiếp theo chạy lại khi
model khả dụng; không tự chuyển model có phí hoặc đổi provider.

## Phiên triển khai trước khi cấu hình key (lịch sử)

Chạy ngày 15/10/2026, kết quả cuối khoảng 11:26 GMT+7. Windows, Python 3.12.13,
uv 0.11.19, Streamlit 1.66.0, Pydantic 2.14.1, pypdf 6.20.1, httpx 0.28.1.
Không có API base/model/key. Không có người dùng/domain reviewer tham gia chấm.

## Lệnh đã thực thi

| Lệnh | Kết quả thực tế |
| --- | --- |
| `uv sync --frozen` | Cài/khóa dependency thành công; không có secrets được tạo |
| `uv run pytest tests -q --junitxml=eval/runs/offline_final.xml` | **47 passed**, 1 browser case deselected, 6.85s |
| `uv run pytest tests/browser -m browser -q --junitxml=eval/runs/browser_final.xml` | **1 passed**, lần cuối 9.26s |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 67 files already formatted |
| `uv run basedpyright` | 0 errors, 0 warnings, 0 notes |
| `UV_PROJECT_ENVIRONMENT=runs/clean-env uv sync --frozen --no-dev` | Virtualenv production sạch: cài 55 package, exit 0 |
| CLI `fixtures` → `inspect` trong clean-env | 11 span, không sinh claims offline, exit 0 |
| Streamlit từ clean-env; GET `/_stcore/health` | `ok`, port local 8501 |
| `uv export --frozen --no-dev --no-hashes --format requirements-txt --output-file requirements.txt` | Export production pins, exit 0 |

XML, ảnh, snapshots và logs nằm dưới `eval/runs/`, mặc định ignored.
`eval/results_actual.csv` giữ 12 attempts trước cấu hình, 2 attempts Gemma và 4 attempts
Laguna từ hai lượt hoàn tất; không chứa key hoặc raw nguồn thật. Các lượt bị ngắt giữ raw
artifact riêng, không suy ra ca chưa hoàn tất để thêm vào bảng.
Không thay kết quả bằng template. Các lượt pytest đỏ trong quá trình TDD không được tính là
failure chất lượng thị trường của LLM.

## Các tình huống offline và tích hợp

| Tình huống | Kỳ vọng | Kết quả thực tế | Đạt/chưa đạt | Điều học được |
| --- | --- | --- | --- | --- |
| Hai nhiệm vụ/câu hỏi với hai nguồn synthetic khác nhau | Cùng pipeline, output gắn nguồn đang đọc | Wire-mock qua adapter thật; quote/claim thay theo input, không case ID | PASS logic | Chưa chứng minh model tự sinh đúng hoặc khả năng tổng quát |
| PDF 2 trang có chữ | Giữ nội dung và page locator | Parser subprocess đọc đúng trang, NFC/hash/offset giữ được | PASS parser | Chưa bao gồm OCR hoặc nhận dạng bảng phức tạp |
| Quote bịa và hash snapshot bị sửa | Từ chối trước tổng hợp; hash sai bị chặn trước model | Pipeline raise citation/source_hash; không fallback | PASS rule | Quote có thật vẫn cần chấm semantic support |
| Source metadata VN nhưng evidence TH | Không dùng làm support cho VN | Regression trước sửa limited, sau sửa insufficient | PASS rule sau sửa | Phải kiểm tra scope ở cấp evidence, không chỉ source |
| Mâu thuẫn cùng dimensions | Hiện xung đột, chặn recommendation | Claim conflicting; recommendation blocked | PASS với output mock | Khả năng model tự phát hiện conflict chưa được đánh giá |
| Gross khác net / dimensions unknown | Không ép thành cùng chỉ số | same_scope false / unknown | PASS rule | So sánh khác định nghĩa không chứng minh mâu thuẫn cùng fact |
| Nguồn dẫn lại và nguồn chưa rõ gốc | Không đếm độc lập từ số URL/domain | Snapshot trùng gom root; gốc unknown giữ independence unknown | PASS rule | Chưa có phát hiện syndication tự động đầy đủ ngoài trùng text/metadata |
| Nguồn kỳ 2023 đăng năm 2026 | Không dùng ngày đăng thay kỳ đo 2025 | freshness no, source unsuitable | PASS rule | Metadata kỳ đo cần xác nhận từ tài liệu |
| Source dài vượt context | Hiện các span bị bỏ qua | context_truncated true, selected chars dưới cap | PASS coverage | Có thể bỏ sót phản chứng; cảnh báo không sửa được thiếu coverage |
| Private/mixed DNS/redirect tới localhost | Không tạo request tới nội bộ | Chặn mọi DNS answer không công khai, pin IP/Host/SNI, chặn redirect | PASS unit HTTP boundary | Không phải pentest toàn hệ thống |
| 401/429, JSON sai, output length | Không lộ body/key; retry có ngân sách | 401 không retry, 429 retry cùng endpoint/model, repair tối đa một lần; output cắt bị từ chối | PASS mock HTTP | Chưa chứng minh provider thật tương thích cấu hình |
| Thiếu key | Không gọi provider, không sample fallback | UI disabled, CLI exit 2, live attempts BLOCKED | PASS UX; live BLOCKED | Chỉ cản phần live, offline vẫn chạy |
| Review/replay/export và phiên riêng | Giữ trước/sau, nguồn, locator, history | Lưu v1/v2 khác nhau; reject/needs_review giữ lại; replay kiểm hash/IDs | PASS integration | Human review là nhãn do người dùng nhập, không phép tự nâng thành verified |

## Kiểm tra bằng trình duyệt thật

Playwright Chromium chạy trên server Streamlit mới, tự dừng server test sau khi chạy.
Đã thao tác nạp fixture, xem nguồn, nhập URL loopback, mở bundle synthetic replay,
mở chính code block chứa quote, ghi needs_review, tải JSON version 2.
Artifacts: `eval/runs/browser/result.json`, `reviewed_synthetic.json`,
`replay_375.png`, `replay_768.png`, `replay_1280.png` và `server.log`.

Ba chiều rộng 375/768/1280 không tràn ngang ở document/main; pageerror = [].
Đã xem ảnh trực tiếp: tiếng Việt hiển thị được, quote/locator/cảnh báo và trạng thái review có mặt.
Đây là UI replay kiểm logic, không live AI. Không có Lighthouse score được đo/báo.
T3 preview timeout hai lần (`Preview automation snapshot timed out after 15000ms.`),
sau đó dùng Playwright local. Những lượt browser đầu dùng server cũ chưa phản ánh module sửa;
suite cuối khởi động server mới để tránh kết quả từ code cũ.

## Live evaluation theo EVALUATION.md

Prompt `evidence-1.0` đóng băng trong `eval/prompt_freeze.json`. Reserved được evaluator
đọc sau freeze, không đưa vào app/pipeline/LLM; không gọi đây là benchmark độc lập chưa thấy trước.
Mỗi case lưu request, snapshots/hash, coverage, expected_evaluator_only, cli.log và result.json.
Code revision là SHA-256 snapshot ứng dụng + dependency, có tiền tố `no_git_snapshot_sha256`,
vì thư mục ban đầu chưa có Git. Chưa có commit hash để báo.

| Tập | Artifact cuối | Actual | Verdict |
| --- | --- | --- | --- |
| T01–T10, dev + reserved | `eval/runs/57884ed08f9b4b5785c0bab74b81c775/` | CLI exit 2: llm_not_configured; request_count=0 | 10 BLOCKED |
| R01: công bố VNG FY2025, kiểm phạm vi công ty/thị trường VN | `eval/runs/2482941b6ed44a94ae310b7bc6db259c/R01/` | HTML tĩnh đã đọc; CLI không gọi LLM vì thiếu cấu hình | BLOCKED |
| R02: deck PDF Sea/Garena FY2025, cạnh tranh riêng TH | `eval/runs/2482941b6ed44a94ae310b7bc6db259c/R02/` | PDF đã đọc; CLI không gọi LLM vì thiếu cấu hình | BLOCKED |

Hai ca thật khác nhiệm vụ/phạm vi. Metadata và gold do agent chuẩn bị, chưa có domain reviewer
xác nhận/chấm; không gọi là nghiên cứu thị trường đã kiểm chứng. Không commit full snapshots
nguồn thật do chưa xác nhận quyền tái phân phối; URLs và giới hạn nằm trong `eval/real_cases.json`.

Kỳ vọng mỗi ca lưu riêng trước CLI → actual thiếu cấu hình → BLOCKED → cần cấu hình tại máy
và chạy lại, đọc mọi material fact/quote/phản chứng trước khi chấm PASS.
Không có live report: citation numerator/denominator = N/A; material support = N/A;
unsupported material count = unknown; missed conflicts = unknown. Không gán 0 lỗi hoặc 100%.
Chưa có baseline/người dùng thử; hypothesis giảm thời gian và tăng độ đúng **chưa đo**.

## Lỗi và giới hạn quan sát trên nguồn thật

Trang `https://ar2025.vng.com.vn/vi/business-report/` trước sửa được đánh dấu ok dù chỉ có
52 ký tự title trong snapshot `eval/runs/real_sources_initial.json`.
Regression HTML-shell tái hiện DID NOT RAISE, sau sửa PASS. Bản cuối
`eval/runs/real_js_final.json`: unsupported, 0 ký tự, yêu cầu JS/OCR hoặc nguồn thay thế.
Đồng thời đã sửa lỗi frozen Exception làm contextlib không thể gán traceback (D006).

**Nhu cầu đọc nội dung trang này vẫn chưa đáp ứng**: app không chạy JavaScript.
Cảnh báo đúng là PASS cho error handling, không phải PASS nghiên cứu nội dung trang.
Đã chọn nguồn công khai HTML tĩnh VNG khác và PDF Sea để chuẩn bị ca thật.
Đây là giới hạn chức năng đã quan sát; chưa có failure semantic live LLM để nộp thay thế.

## Tự rà soát bàn giao

- App/src không đọc eval/cases, eval/expected hoặc branch theo case ID; mock chỉ trong tests.
- Không source text nào được chạy như lệnh/HTML; LLM không có tool execution.
- Quote, scope và semantic support tách riêng; độc lập unknown, không confidence % giả.
- Chưa triển khai nhiều agent, search rộng, database vector, doanh thu dự báo hoặc accounts.
- Không tạo agent phụ theo yêu cầu người dùng. Review code/security/UX thực hiện trong phiên chính;
  không tuyên bố có review độc lập bởi nhiều reviewer.
- Chưa đủ nghiệm thu Mission 2: cần upstream live khả dụng, ≥5 ca live có report, hai ca nguồn thật,
  chấm semantic/completeness, ca failure AI thật và video. Chưa public/deploy.
