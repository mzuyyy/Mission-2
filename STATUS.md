# Trạng thái Gamota Mission 2

## Sửa UI chọn nền tảng/ngày theo yêu cầu (15/10/2026)

- `src/gamota_research/ui_input.py`: nền tảng dùng `st.multiselect` (bấm mở bảng tích chọn,
  8 gợi ý + ô tự nhập thêm); từ ngày/đến ngày dùng `st.date_input` kèm checkbox
  "Chưa biết" (mặc định unknown, không tự điền). Contract giữ nguyên kiểm tra từ ngày ≤ đến ngày.
- Kiểm tra thật: `pytest` **67 passed, 1 deselected**; AppTest render không exception,
  multiselect mặc định `['Android']`, date None+disabled; kịch bản nhập đủ (kèm nền tảng
  tự nhập + khoảng ngày) không lỗi, khoảng ngày ngược báo lỗi đúng.

## Deploy online đã xác minh một phần (15/10/2026, khoảng 16:55–17:10 GMT+7)

- App deploy từ `mzuyyy/Mission-2@main/app.py`, Python 3.12:
  **https://mission2.streamlit.app/**. Không sửa setting nào trên host.
- Xác minh thật từ máy này (curl + tab browser T3, profile đã đăng nhập của chủ tài khoản):
  DNS phân giải `35.201.127.49`; trang chủ ẩn danh HTTP 200 sau 2–3 redirect handshake
  phiên (cookie jar), trả đúng vỏ app Streamlit; `/api/v2/app/status` trả
  `viewerAuthEnabled=false`, `streamlitVersion=1.66.0` — không bắt viewer đăng nhập.
  Kết luận "đòi login" trước đó là sai: các 303 ban đầu chỉ là handshake phiên ẩn danh.
- Trình duyệt đã render đầy đủ UI một lần: tiêu đề "Gamota · Nghiên cứu có căn cứ ·
  Streamlit", form câu hỏi/phạm vi, nguồn URL/PDF, 4 tab Kết quả/Bằng chứng/Nguồn/Kiểm tra.
- Hạn chế chưa khắc phục: container free tier ngủ khi không dùng; lúc kiểm tra lại,
  `/_stcore/health` trả vỏ SPA của host thay vì `ok`, và UI có lúc chỉ hiện khung trống
  trong lúc wake. Chưa bắt được lần render ẩn danh end-to-end hoàn chỉnh lần hai.
  Không ghi health `ok` khi chưa quan sát thật.
- Tiếp theo: người chấm mở link khi container thức; quay video demo; giữ nguyên
  `.env`/key local, secrets chỉ nằm trên host.

## Chuẩn bị bài nộp public và online theo yêu cầu mới (15/10/2026)

- Người dùng đã yêu cầu rõ repo public và deploy online; chỉ dẫn cũ chưa xuất bản
  đã được thay thế cho phạm vi này. GitHub API xác nhận `private=false`, repo
  `https://github.com/mzuyyy/Mission-2`. Bản sửa PDF đã push ở `0dfb9b2`.
- Quét 120 blobs lịch sử và 103 tệp tracked trước public: không thấy API key local
  hoặc mẫu token/private key đã quét; không có raw runs/snapshots tracked.
  Đây là kiểm tra secrets có giới hạn, không phải chứng nhận an ninh toàn diện.
- CI Linux commit `f34a6a8`: **SUCCESS**, run `38711272415`; 67 passed, 1 deselected,
  7.48s; Ruff/type sạch, `uv sync --frozen --no-dev` và Streamlit health `ok`.
  CI không có API key và không gọi live LLM.
- Bộ bài nộp `docs/SUBMISSION_TEST_CASES.md`: 8 ca logic và ca nguồn thật/failure,
  không tính fixture/mock là live. Lượt chọn lọc **28 passed, 0.87s**,
  browser **1 passed, 10.55s**, XML `eval/runs/submission_scenarios.xml` và
  `submission_browser.xml`.
- Đã tạo `deliverables/Gamota_Mission_2_MVP.pptx`: 7 slides, 7 trang notes,
  timeline dự kiến 280 giây; render lại file PPTX cuối và xem từng slide.
  Ảnh UI là synthetic replay được gắn nhãn. Chưa quay video thật.
- Đã chuẩn bị `.streamlit/secrets.example.toml` và hướng dẫn Community Cloud.
  Streamlit đã đăng nhập qua Google, nhưng Create app báo: "You must be connected
  to GitHub to deploy an app." Đã mở Connect to GitHub, đang ở trang GitHub login
  chờ chủ tài khoản; chưa tạo app hoặc xác nhận URL online. Không báo deploy thành công từ CI.
- Bài nộp đã push ở `3b1deac`; truy cập ẩn danh GitHub repo và PowerPoint đều HTTP 200,
  SHA-256 file tải về khớp bản local. CI trên commit bài nộp cũng SUCCESS,
  run `38712252116`. Kiểm tra lại 108 tệp working tree, gồm XML trong PPTX, không
  thấy key local hoặc mẫu secret đã quét. Không đưa inspect/debug files vào bài nộp.
- Tiếp theo: dùng phiên hosting đã đăng nhập để deploy, cấu hình secrets riêng trên
  host, kiểm UI từ URL public và cập nhật README. Gemini e1.2 vẫn chưa được chấm
  ngữ nghĩa sau sửa vì lượt live trước trả HTTP 429.

## Bản sửa cấu trúc PDF sau push (15/10/2026, khoảng 15:45–15:48 GMT+7)

- Tái hiện bằng PDF synthetic vẽ số khác thứ tự vị trí: parser cũ mất hàng/cột;
  3 regression mới FAIL trước sửa. Trang thực 4/5 Sea deck có nhãn Garena nằm
  sát số Monee trong plain text; layout giữ cột đúng. Trang 4 cũ chưa bị chia nên
  không quy toàn bộ lỗi cho retrieval.
- Đã chuyển PDF sang pypdf layout, giữ trang nguyên vẹn khi chọn context;
  trang không vừa ngân sách quote/context được bỏ nguyên trang và ghi coverage.
  Prompt evidence-1.2 yêu cầu abstain số khi nhãn/cột/kỳ mơ hồ, không suy thiếu dữ liệu
  ở phần đã chọn thành khẳng định thiếu trong toàn bộ tài liệu.
- Tự kiểm phát hiện layout mặc định bỏ chữ xoay: thêm test đỏ rồi bật giữ chữ xoay;
  5 regression PDF/HTML mới PASS. Các module thay đổi dưới 150 dòng code/module;
  không thêm dependency, agent hoặc thay hợp đồng JSON.
- `uv run pytest tests -q --junitxml=eval/runs/pdf_layout_offline_final.xml`
  → **67 passed, 1 deselected, 10.06s**. Test dùng nguồn synthetic/mock.
  Browser replay/review/export thật trong Chromium → **1 passed, 12.35s**;
  XML `eval/runs/pdf_layout_browser.xml`. Ruff check/format và basedpyright sạch.
- Evaluator nguồn thật `24e3d68b0c3745b58ee1abb8528e0d05`: R01/R02 BLOCKED HTTP 429,
  CLI exit 2, lần lượt 4/2 requests. Thử lại riêng PDF sau đó:
  `e91bc1ec57d241fc8814855b5281e6d0`, R02 BLOCKED HTTP 429, 2 requests.
  Gemini/config/ngân sách giữ nguyên, không fallback. Không có report e1.2 để chấm.
- PDF thật parse đủ 25 trang, 32.819 ký tự, offsets hợp lệ; retrieval chọn 7.821 ký tự,
  bỏ 17 trang và ghi coverage. Raw PDF/snapshots chỉ lưu local trong thư mục ignored.
  CLI `ingest --pdf` và `inspect` chạy thật exit 0; 8 spans được kiểm quote/page/offset
  bằng code, audit ở `runs/pdf_layout_fix/locator_audit.json` (không LLM/không claims).
- Chưa thể khẳng định model đã hết lỗi ghép số hoặc chấm semantic/completeness PASS.
  Bước tiếp theo: chạy lại R02 khi quota cho phép và đối chiếu từng fact với đúng cột/kỳ.
  Bản sửa đang local, chưa commit/push thêm hoặc deploy.

## Đã đẩy Git theo yêu cầu người dùng

- Đã khởi tạo Git local, nhánh `main`, giữ nguyên code và dữ liệu có sẵn.
- Đã tạo repository riêng tư `https://github.com/mzuyyy/Mission-2` bằng tài khoản
  GitHub đã đăng nhập. Chưa deploy ứng dụng.
- Commit gồm MVP, tests, fixtures giả lập, eval pack và tài liệu. `.env`, backup key,
  snapshots/logs chạy thử (`runs`, `eval/runs*`) và script chẩn đoán thử nghiệm giữ local.
- Bộ test offline chạy lại trước commit: **62 passed, 1 deselected, 10.68s**,
  XML ở `eval/runs/git_publish_offline.xml`. Ruff check đạt; basedpyright không lỗi/cảnh báo.
- Đã push commit MVP `637c8f4` lên `origin/main`. GitHub API xác nhận SHA remote
  `637c8f4f4083b1b0e6436a384352c4511154896a` trùng local, repo `private=true`.
  Kiểm tra nội dung staged không thấy key; không đưa raw snapshots/logs vào Git.
- Bước tiếp theo của MVP vẫn là review lỗi ngữ nghĩa PDF và hoàn tất đánh giá còn thiếu;
  push repo không đồng nghĩa nghiệm thu chất lượng hoặc deploy.

## Cập nhật hiện tại sau chỉ dẫn giữ Gemini (15/10/2026, khoảng 14:07 GMT+7)

- Cấu hình đã xác nhận: Google endpoint, `gemini-2.5-flash-lite`, key có tại máy;
  context 8.000 ký tự, output cap 2.500 token/request, tối đa 4 requests gồm retry.
  2.500 là mặc định do ứng dụng đặt, không phải giới hạn model. Không tăng cap/ngân sách request hoặc cấu hình billing.
  Chỉ dẫn chuyển Groq đã được người dùng thay bằng giữ Gemini; cấu hình cuối giữ Gemini.
- Đã sửa: evidence draft có thể chỉ chọn source/span IDs; code lấy nguyên văn quote từ
  snapshot. Quote model tự gửi vẫn kiểm exact. Prompt e1.1 gọn hơn, retry output cắt có
  chỉ dẫn rút gọn, retry citation/inference nhận feedback. Thêm cảnh báo evidence chọn lọc.
- Lượt `fa5bafbbe8004b5b8509274e1a56d59e`: R01/R02 **đều CLI exit 0**, 5 claims mỗi ca,
  quote checks **5/5** và **6/6**, dùng 4 và 3 requests. R02 chọn 7.954 ký tự, bỏ 15 spans;
  coverage báo rõ context_truncated. Recommendations đều blocked. Chưa có human review.
- Lượt 3 dev fixture gọi Gemini thật `7acbfef913af497b997b72426a83a378`: T03 exit 0,
  3/3 quotes, 3 requests; T01 BLOCKED HTTP 503 (2 requests), T04 BLOCKED HTTP 429
  (3 requests). Đây là synthetic inputs/live model, không phải nghiên cứu thị trường thật.
- **Chất lượng PDF chưa đạt**: R02 có claims c1/c2 gán sai Bookings và kỳ đo từ biểu đồ.
  Trợ lý đối chiếu nguồn phát hiện lỗi; raw evaluator vẫn BLOCKED đợi người chấm.
  Không tính tất cả report là PASS, không báo semantic support 100%.
- Regression thật: `uv run pytest tests -q --junitxml=eval/runs/gemini_output_fix/offline_after.xml`
  → **62 passed, 1 deselected, 10.66s**. Browser suite → **1 passed, 11.41s**.
  Ruff/type checks sạch sau sửa; không tạo agent phụ, không publish/deploy.
- Mốc lỗi giữ nguyên: `6b663267075b4fcb9e4ef1454bb4eca6` R01 exit 0, R02 HTTP 503;
  `gemini_output_fix/r02_retry` HTTP 503; `r02_context_8000` sinh report nhưng ghép số sai.
- Tiếp theo: người đọc nguồn review/sửa các fact của PDF, cải thiện bảo toàn cấu trúc bảng;
  chạy lại T01/T04 khi quota/dịch vụ cho phép; còn thiếu ≥5 report live được chấm đạt,
  reviewer độc lập, baseline tốc độ và video. Không dán key vào chat.

Các phần bên dưới là lịch sử triển khai; nếu khác cấu hình hiện tại thì dùng mốc cập nhật trên.

Phiên triển khai: 15/10/2026 (GMT+7). Repo lúc bắt đầu chỉ có tài liệu/fixture, chưa có code
và không có thư mục Git. Không reset/xóa dữ liệu có sẵn; không tạo agent phụ, remote hoặc deployment.

## Đã hoàn thành phần triển khai offline

- Python + Streamlit, contracts Pydantic, dependency `uv.lock` và production `requirements.txt`.
- URL HTML/text UTF-8/PDF: pin IP sau kiểm tra mọi DNS answer, redirect, cap bytes/pages/chars;
  worker deadline bao gồm DNS và PDF. Giữ snapshot NFC, SHA-256, offsets/trang/ngữ cảnh.
- Retrieval lexical tiếng Việt, đa nguồn và caveat; ghi span bỏ qua, nguồn lỗi/partial và context cap.
- Pipeline hai lượt extraction/synthesis; adapter HTTPS OpenAI Chat Completions một endpoint/model
  cấu hình; retry/JSON repair nằm trong ngân sách chung, không sample fallback hay đổi provider.
- Kiểm quote/hash/span/IDs, fact material cần support; inference cần premise/assumptions/reasoning.
  Scope từng evidence, kỳ dữ liệu, so sánh gross/net và dimensions unknown; chặn lời khuyên bị ảnh hưởng.
- Source assessment theo câu hỏi/claim với rationale/provenance, lineage trùng/khai báo/unknown,
  không confidence %. Semantic support vẫn phải được người đọc chấm.
- UI tiếng Việt bốn tab: nhập câu hỏi/phạm vi, đọc nguồn offline, mở đúng quote, cảnh báo coverage,
  live/fixture/replay rõ ràng. Source text hiển thị như text/code thuần.
- Review accept/needs_review/reject và sửa text: version trước/sau, history trong export.
  Sửa text cần chấm lại; rejection ảnh hưởng recommendations. JSON snapshot + Markdown anchors.
- CLI dùng cùng pipeline; evaluator tách expected, đóng băng prompt/input, lưu artifact.
- Browser test tự khởi động server mới, tắt live trong môi trường test; không dùng module server cũ.

## Lệnh và kết quả chạy thật

- Lượt Gemini flash-lite + synthesis retry (15/10/2026, `8f2a8eb0…`):
  R01 **ra report live đầu tiên**: 8 claims, 3 evidence, 2 requests, ~10K tokens,
  `live: 8 claims`. Chấm thủ công trên nguồn thật: 3/3 quote khớp nguyên văn;
  6/7 fact được hỗ trợ (limited), 1 claim (Zalopay 413%) diễn giải phạm vi rộng hơn
  nguồn nhưng đã bị đánh `insufficient`; inference thiếu dữ liệu có premise/reasoning
  đầy đủ, recommendation `blocked=true`. R02 FAIL `provider_incomplete` (2 req,
  ~28K tokens): payload PDF lớn + output chạm cap 2500 cả 2 lần. Đang hỏi người
  dùng về tăng `MAX_OUTPUT_TOKENS` ở thời điểm đó; mốc hiện tại giữ cap và sửa luồng trích xuất.
- Lượt Gemini theo yêu cầu người dùng (key do người dùng thêm vào `.env`;
  model `gemini-2.5-flash`, base OpenAI-compat của Google):
  `uv run python eval/run_evaluation.py --cases eval/real_cases.json --split real`.
  Probe 1 request trước đó: HTTP 200, JSON hợp lệ, cả `max_completion_tokens`
  và `max_tokens` đều cho `finish_reason=stop` (một lần lẻ bị `length` ở 3 tokens
  với cap 200, không tái hiện ở cap 1000). Ba runs liên tiếp đều chưa ra report:
  `9288e27f…`: R01/R02 FAIL `provider_incomplete` (2 và 1 request);
  `2aeca5e9…`: R01 FAIL `inference: VNG_INF1 thiếu premise/giả định/lập luận`
  (extraction đã qua sau 1 retry), R02 FAIL `provider_incomplete` (2 req, ~28K tokens);
  `854eb01d…`: R01 BLOCKED HTTP 503 (3 req), R02 FAIL `dangling_id:
  GarenaDataInsufficiency_1` (4 req). Diagnostic đơn lẻ cùng payload cho HTTP 200
  `finish_reason=stop` — lỗi không ổn định theo từng lần gọi. Kết luận: validator
  bắt đúng (quote/inference/dangling), nhưng output của 2.5-flash thiếu ổn định
  cho pipeline strict. Đang hỏi người dùng trước khi đổi model cũ hơn.
- Chạy lại sau yêu cầu tiếp tục: `uv run python eval/run_evaluation.py --cases
  eval/real_cases.json --split real`, không sudo, dùng môi trường Windows hiện có.
  Cấu hình người dùng lúc chạy là `poolside/laguna-s-2.1:free`, không còn Gemma;
  giữ nguyên `.env`, timeout 45 giây và tối đa 4 request/lượt.
  Artifact `eval/runs/64a2c5b70eef48b28a0d17c79a5de846/`: R01/R02 **2 BLOCKED**,
  mỗi CLI exit 2 với HTTP 429, không report. Evaluator exit 0 nghĩa đã lưu kết quả,
  không có nghĩa hai ca đạt. Nguồn HTML/PDF vẫn đọc được.
- Kiểm tra artifacts đã có trước khi chạy: `e68dc038dec145e6827ca47c7a64b59f`
  có R01 BLOCKED 429, R02 **FAIL** `citation: E1: quote không khớp span đã chọn.`
  Không có raw extraction để kết luận model đã dịch/paraphrase hay chọn nhầm span.
  Lượt `8254ffb25a1b4221b0a967ac9d5773d6` chỉ có R01 BLOCKED timeout và R02 chưa có
  result; giữ nguyên trạng thái chưa hoàn tất, không tự điền kết quả R02.
  Chưa có report live thành công hoặc chấm semantic support.
- Phiên này chỉ chạy evaluator và cập nhật tài liệu/CSV, không sửa mã ứng dụng,
  không chạy lại pytest/browser. Kết quả offline 47 passed bên dưới thuộc phiên trước.
- Lượt mới sau khi người dùng cấu hình OpenRouter: `uv run python eval/run_evaluation.py
  --cases eval/real_cases.json --split real`: R01/R02 **2 BLOCKED**, CLI exit 2,
  `provider_retryable: Provider trả HTTP 429`. Nguồn HTML/PDF đọc được; không có report.
  Artifact: `eval/runs/4649b693afb8403fad753b7a532f0b31/`.
- Chẩn đoán live riêng (không mock): GET `/api/v1/key` trả **200**; một POST completion nhỏ
  trả **429**, metadata ghi Google AI Studio và `temporarily rate-limited upstream`.
  Model giữ nguyên `google/gemma-4-31b-it:free`; không sửa `.env`, không nâng ngân sách,
  không chuyển model/provider. Chỉ lưu metadata đã loại secrets trong `diagnostic.json`.
- Regression phiên OpenRouter: `uv run pytest tests -q
  --junitxml=eval/runs/openrouter_offline_regression.xml`: **47 passed, 1 deselected, 6.47s**.
  Đây là test offline/mock, không chứng minh live LLM đã hoạt động.
- `uv sync` và `uv sync --frozen`: exit 0; runtime Python 3.12.13, Streamlit 1.66.0,
  Pydantic 2.14.1, pypdf 6.20.1, httpx 0.28.1.
- `uv run pytest tests -q --junitxml=eval/runs/offline_final.xml`: **47 passed**,
  1 browser case deselected, 6.85s. Unit/integration dùng synthetic/mock, không phải market research.
- `uv run pytest tests/browser -m browser -q --junitxml=eval/runs/browser_final.xml`:
  **1 passed**, lần cuối 9.26s. Quote code block, review v2, JSON download đã được thao tác thật.
- `uv run ruff check .`: All checks passed.
- `uv run ruff format --check .`: 67 files already formatted.
- `uv run basedpyright`: 0 errors, 0 warnings, 0 notes.
- `UV_PROJECT_ENVIRONMENT=runs/clean-env uv sync --frozen --no-dev`: cài 55 packages vào
  môi trường production sạch; CLI fixtures/inspect exit 0, 11 spans, không claims.
- Streamlit khởi động từ clean-env, local `http://127.0.0.1:8501`; health endpoint trả `ok`.
- Export production pins: `uv export --frozen --no-dev --no-hashes --format requirements-txt --output-file requirements.txt`, exit 0.
- `uv run python eval/run_evaluation.py --split all --freeze-prompt`:
  T01–T10 **10 BLOCKED**, mỗi CLI exit 2, thiếu cấu hình LLM, 0 request provider.
- `uv run python eval/run_evaluation.py --cases eval/real_cases.json --split real`:
  R01/R02 **2 BLOCKED**, nguồn thật đã đọc, chưa gọi LLM.
- Raw evaluator lịch sử trước khi có key:
  `eval/runs/57884ed08f9b4b5785c0bab74b81c775/` và
  `eval/runs/2482941b6ed44a94ae310b7bc6db259c/`.
  Bảng đã rút gọn/redact: `eval/results_actual.csv`.
- Browser evidence ở `eval/runs/browser/`: ba viewport 375/768/1280, không overflow main/document,
  pageerror=[]; dữ liệu synthetic replay và mock HTTP được ghi rõ.
- Nguồn thật: VNG snapshot FY2025 HTML ok, 2.947 ký tự; Sea PDF ok, 25 trang, 18.565 ký tự.
  Snapshots thật ở thư mục ignored, chưa công bố quyền phân phối.

## Lỗi quan sát và quyết định

- CLI Typer ban đầu không nhận --out; console cp1252 lỗi khi in tiếng Việt.
  Đã khai báo options và UTF-8; CLI thật đã qua.
- Trang VNG annual report JS-only ban đầu bị ghi ok dù chỉ title 52 ký tự.
  Đã có regression đỏ/xanh; bản cuối unsupported, 0 ký tự. Nội dung trang vẫn chưa đọc được.
- Typed exception frozen gây TypeError khi contextlib gán traceback; đã đổi Exception phù hợp,
  regression và ingestion lỗi đã qua.
- Evidence khác quốc gia từng chỉ limited, hash sai chỉ phát hiện sau extraction.
  Đã kiểm scope evidence và hash trước send; regression PASS.
- Browser snapshot từng hiện UI cũ dù source đã đổi; server mới và widget keys ổn định đã qua QA.
- Decision records: D004–D011 trong `docs/DECISIONS.md`. Báo cáo chi tiết: `docs/TEST_RESULTS.md`.

## Blocker và giới hạn còn lại

- Người dùng yêu cầu chuyển `.env` sang Google Gemini (15/10/2026).
  Cấu hình hiện tại: base `https://generativelanguage.googleapis.com/v1beta/openai`,
  model `gemini-2.5-flash`, key trống (`live_ready=false`) chờ người dùng thêm key.
  Cấu hình Groq cũ (base/model/key) được giữ nguyên trong `.env.bak.groq-20261015`,
  không mất dữ liệu. Lý do: Groq free giới hạn 8K TPM gây HTTP 413 với payload R02
  (~9–10K tokens); Gemini free tier kỳ vọng TPM cao hơn, cần probe 1 request sau khi
  có key để xác minh. Không tự đổi model khi lỗi; đây là yêu cầu tường minh của người dùng.
- Người dùng đã cấu hình `.env` với OpenRouter; key được endpoint xác thực chấp nhận.
  **Lượt hiện tại: Laguna HTTP 429**, không còn bị chặn vì thiếu key.
  Chi tiết Google AI Studio upstream trước đó chỉ áp dụng cho lượt Gemma đã chẩn đoán;
  chưa có metadata để quy lỗi Laguna cho cùng upstream đó.
  `.env` được giữ nguyên và ignored; không in key, không bật billing, không fallback mẫu.
  Các dòng `llm_not_configured` trong artifacts cũ là lịch sử trước khi có cấu hình.
- Chưa có ≥5 ca live report, hai câu hỏi live thật, semantic support/completeness grading,
  hoặc failure semantic live LLM. Không đủ điều kiện đánh dấu toàn bộ ACCEPTANCE hoàn tất.
- Reserved được evaluator đọc sau prompt freeze; không tuyên bố là benchmark độc lập chưa thấy trước.
- Chưa OCR/JS rendering/chart recognition; UTF-8 và response không nén. PDF bảng và retrieval
  dài có thể thiếu quan hệ/phản chứng. Windows worker chưa có hard memory sandbox.
- Metadata nguồn thật chưa tự suy ra đầy đủ. Model có thể dùng quote sai ý; locator checks không
  chứng minh semantic support, coverage warning không chứng minh completeness.
- Chưa đo baseline/tốc độ với người dùng; không có tỷ lệ support, unsupported count hoặc
  missed conflict live đã được chấm. Giữ N/A/unknown, không gán 0 hay 100%.
- Chưa có quota toàn dịch vụ/accounts; demo public cần host đặt ngân sách tổng/quyền truy cập.
- Chưa có Git public, deploy online hoặc video; chỉ chuẩn bị cấu hình và tài liệu.

## File chính và bước tiếp theo

- `app.py`, `src/gamota_research/`, `tests/`, `examples/request.json`.
- `eval/run_evaluation.py`, `eval/evaluation_support.py`, `eval/real_cases.json`,
  `eval/prompt_freeze.json`, `eval/results_actual.csv`.
- `pyproject.toml`, `uv.lock`, `requirements.txt`, `.env.example`, `.streamlit/config.toml`,
  `DESIGN.md`, README và docs TEST_RESULTS/DECISIONS/DEPLOYMENT.

Tiếp theo: chạy lại evaluator khi upstream model đã hết giới hạn; nếu muốn đổi model
thì chọn rõ trong cấu hình tại máy, không tự đổi khi lỗi. Sau khi sinh được report,
đọc/chấm mọi material claim và phản chứng, bổ sung failure thực tế,
sau đó quay video. Chỉ public/push/deploy khi người dùng yêu cầu. Ba câu Mission 2 trả trong chat,
không tạo file trả lời riêng.

