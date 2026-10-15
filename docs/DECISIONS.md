# Nhật ký quyết định

## D001 Phạm vi đầu tiên
Trạng thái: chốt trước triển khai.
Quyết định: nguồn do người dùng cung cấp, một thị trường mỗi lượt, cùng pipeline cho câu hỏi mới.
Lý do: ưu tiên kiểm chứng nhận định thay vì mở rộng tìm kiếm.
Đánh đổi: thao tác chọn nguồn còn thủ công.
Bằng chứng thực nghiệm: chưa có.

## D002 Công nghệ
Trạng thái: chốt trước triển khai, cần thử dependency/provider.
Quyết định: Python + Streamlit + JSON + một LLM qua adapter.
Lý do: giảm phần hạ tầng trong 3 ngày.
Bằng chứng thực nghiệm: chưa có; không gọi đây là thay đổi do lỗi quan sát.

## D003 Đánh giá nguồn
Trạng thái: chốt trước triển khai.
Quyết định: dimensions có lý do theo claim, không điểm confidence %.
Lý do: source reputation không đồng nghĩa claim support.
Bằng chứng thực nghiệm: chưa có.

## Mẫu cho thay đổi mới

### D015 Tạo repository riêng tư theo yêu cầu đẩy code
- Người dùng yêu cầu tự tạo repo tên Mission 2 và push; tên GitHub dùng `Mission-2`.
  Chọn private vì chưa có chỉ dẫn công khai; không deploy ứng dụng.
- Quan sát thật: GitHub CLI tạo `mzuyyy/Mission-2`; push nhánh `main` thành công.
  API trả `private=true` và SHA `637c8f4f4083b1b0e6436a384352c4511154896a`
  trùng commit MVP local. Đây là kiểm chứng việc lưu code, không phải chất lượng nghiên cứu.
- Giữ `.env`, backup key, raw snapshots/logs và probe scripts tại máy. Bổ sung ignore
  `eval/runs_*` và `eval/runs-*`; kiểm tra staged không thấy key trước commit.
- Kiểm tra trước push: 62 test offline đạt, 1 browser test deselected; Ruff check đạt,
  basedpyright không lỗi/cảnh báo. Không chạy thêm live LLM cho thao tác Git.

### D014 Giữ Gemini, chọn span và tách ngân sách input/output
- Quan sát thật: trace `eval/runs/gemini_output_fix/before_attempt_*.json` cho R02:
  extraction đầu finish=stop nhưng quote không khớp, các lượt kế finish=length với cap 2.500.
  Trước sửa retry length gửi request giống hệt; ba regression mới FAIL vì quote bắt buộc
  và request retry không đổi, sau sửa PASS. Đây là lỗi thiết kế/cấu hình app, không chứng
  minh Gemini có giới hạn tối đa 2.500 token. Cách giải thích trước đó đã lẫn hai giới hạn.
- Người dùng chốt giữ Gemini sau yêu cầu chuyển Groq bị ngắt. Cấu hình cuối giữ Google,
  gemini-2.5-flash-lite; output 2.500 và request 4 không tăng. Context giảm40000→8000 ký tự
  sau phép thử R02 tạo report; snapshot đầy đủ được giữ, spans bỏ qua/caveat đều trong coverage.
- Thay đổi: draft chọn source/span IDs, code lấy nguyên văn span để tạo quote/locator/hash.
  Quote tường minh từ model vẫn exact-check. Prompt e1.1 yêu cầu output gọn và chọn lọc;
  retry length thêm chỉ dẫn rút gọn, citation/synthesis retry thêm feedback mã lỗi.
  Không có nhánh theo câu hỏi/case ID; expected không vào pipeline. Freeze mới được ghi rõ,
  không gọi dữ liệu đã xem là benchmark chưa thấy trước.
- Lượt `fa5bafbbe8004b5b8509274e1a56d59e` tạo R01/R02: quote 5/5 và6/6; cap giữ nguyên.
  Context R02 chọn 7.954 ký tự, bỏ 15 spans. Lượt trước R02 HTTP503; giảm context rồi thành công
  chỉ là quan sát, chưa chứng minh quan hệ nhân quả của lỗi dịch vụ.
- Chất lượng còn lỗi thật: R02 ghép Bookings/kỳ đo sai từ chart nhiều cột. Citation đúng
  không sửa semantic mapping. Raw verdict vẫn BLOCKED vì chưa có human review; lỗi nội dung
  được lưu riêng, không dùng nhãn PASS có điều kiện thay cho nghiệm thu.
- Kết quả offline:62 passed; browser:1 passed. Không đo hypothesis tốc độ/độ đúng người dùng.

### D011 Phân biệt lượt Laguna bị giới hạn, citation failure và lượt bị ngắt
- Quan sát: cấu hình người dùng đã đổi sang `poolside/laguna-s-2.1:free`.
  Lệnh evaluator chạy lại tạo `eval/runs/64a2c5b70eef48b28a0d17c79a5de846/`:
  R01/R02 BLOCKED HTTP 429, CLI exit 2. Evaluator exit 0 chỉ xác nhận việc lưu kết quả.
- Lượt hoàn tất đã có `e68dc038dec145e6827ca47c7a64b59f` ghi R02 FAIL citation E1
  không khớp span. Lượt `8254ffb25a1b4221b0a967ac9d5773d6` chỉ có R01 timeout;
  R02 thiếu result. Không viết tiếp/ghi đè hoặc tính ca chưa xong là PASS/FAIL.
- Quyết định: giữ nguyên model/config/ngân sách và kiểm quote chính xác; không làm lỏng
  locator để vượt lỗi. Chưa sửa thuật toán vì không có raw extraction chứng minh nguyên nhân.
  Các dòng failure được giữ trong kết quả, không bị thay bởi lượt retry sau.
- Đánh đổi: chưa có báo cáo live cho người dùng kiểm chứng; cần provider khả dụng và
  chẩn đoán extraction có kiểm soát trước khi thiết kế cách sửa. Không quy lỗi Laguna
  cho Google AI Studio từ diagnostic Gemma trước đó. Không sửa mã ứng dụng ở phiên này.

### D010 Giữ nguyên model khi OpenRouter trả giới hạn upstream
- Quan sát ngày 15/10/2026: R01/R02 dùng key người dùng cấu hình, production CLI đều
  exit 2 với HTTP 429. GET key HTTP 200; diagnostic completion HTTP 429 ghi rõ
  provider Google AI Studio và `temporarily rate-limited upstream`.
- Bằng chứng: `eval/runs/4649b693afb8403fad753b7a532f0b31/`, gồm diagnostic.json đã
  loại secrets. Không có live report, không có kết quả chấm semantic/completeness.
- Quyết định vận hành: giữ `google/gemma-4-31b-it:free`, endpoint, `.env` và ngân sách;
  dừng thử thêm toàn bộ fixture để tránh request vô ích. Không fallback hoặc bật billing.
  Đây là xác nhận chính sách sẵn có từ lỗi thật, không phải thay đổi thuật toán.
- Đánh đổi: chưa có kết quả live để chứng minh luồng LLM xuyên suốt. Thử lại khi model khả dụng;
  lựa chọn model khác phải được cấu hình rõ. Chưa chứng minh các tham số sinh được provider nhận
  thành công chỉ từ việc key hợp lệ.
- Regression offline phiên này: 47 passed, 1 deselected (6.47s); không thay thế live evaluation.

### D008 Kiểm tra trên server mới và giữ panel replay ổn định
- Quan sát: các browser attempt trước (`eval/runs/browser/attempt_*.log`) có lỗi
  upload/replay không thao tác được. Snapshot vẫn hiện expander cũ trong khi source
  đã đổi sang container; AppTest/backend test không phát hiện được trạng thái server này.
- Thay đổi: replay có panel luôn hiển thị và key uploader ổn định; browser test tự
  khởi động server mới với `fileWatcherType=none`, cổng riêng và cấu hình live rỗng.
  Test chờ source rerender, kiểm tra chính phần code quote thay vì text claim trùng quote.
- Kết quả: browser flow đã PASS, mở quote [0,33), lưu needs_review version 2,
  tải JSON, kiểm tra 375/768/1280 không tràn ngang và không có pageerror.
- Đây là synthetic replay/wire mock, không phải hai lượt live LLM hoặc phỏng vấn người dùng.

### D009 Kiểm tra scope từng evidence và hash trước khi gửi
- Quan sát regression: evidence cho TH trong source metadata VN trước sửa chỉ bị limited;
  snapshot đổi text/hash cũ chỉ bị phát hiện sau lượt extraction. Hai test integrity đã FAIL
  đúng các hành vi này trước khi sửa, sau sửa PASS.
- Thay đổi: kiểm hash/size mọi snapshot trước gọi model; kiểm scope/kỳ từng evidence bên cạnh
  metadata tổng. Mismatch rõ hạ insufficient. Giới hạn payload gồm metadata/evidence.
- Rút gọn validator thành các hàm claim/conflict/premise/recommendation có trách nhiệm riêng;
  mọi module ứng dụng dưới 250 dòng code không tính comment/dòng trống.
- Source summary chỉ có thể strong khi có phương pháp/lợi ích/xuất xứ/kỳ/phạm vi đầy đủ;
  đó là nhãn suitability theo metadata, không chứng minh semantic support hay độc lập.
- Review/save parse lại contracts; lỗi network/auth/timeout trong evaluator giữ BLOCKED,
  không tự tính là failure chất lượng model. CLI quá deadline vẫn có artifact để ghi nhận.

### D006 Lỗi thật khi đọc HTML phụ thuộc JavaScript
- Thời điểm: 15/10/2026, thử nguồn công khai bằng CLI.
- Quan sát trước sửa: `eval/runs/real_sources_initial.json` ghi trang
  `https://ar2025.vng.com.vn/vi/business-report/` là ok với 52 ký tự,
  toàn bộ là title, không có nội dung báo cáo. PDF Sea cùng lượt đọc được 25 trang,
  snapshot 18.565 ký tự. Không có LLM trong lượt này.
- Thay đổi: loại head/title khỏi body được đọc; body rỗng hoặc chỉ title báo unsupported
  và đề nghị nguồn HTML tĩnh/PDF thay thế. Không thêm JS rendering/bypass vào MVP.
- Lỗi thứ hai quan sát qua traceback chạy thật: `ResearchError` dùng dataclass frozen
  làm contextlib không thể gán `__traceback__`, chuyển lỗi nguồn thành worker failure.
  Đổi sang typed Exception thông thường. Regression test đã tái hiện lỗi này trước sửa.
- Bằng chứng test: test_html_shell_does_not_count_title_as_read_content từng FAIL
  “DID NOT RAISE”, sau sửa PASS; test_research_error_propagates_through_stream_context
  từng FAIL TypeError tại contextlib.py:191. Bộ offline sau sửa: 31 passed.
- Giới hạn còn lại: nội dung chỉ có sau JS không đọc được. Cảnh báo đúng không đồng nghĩa
  đáp ứng yêu cầu nghiên cứu nội dung trang đó. Live semantic quality vẫn BLOCKED thiếu cấu hình.

### D007 Review và export giữ trước/sau, không nâng nhãn theo accept
- Quan sát: pipeline wire-mock và storage tests PASS; đã lưu hai version khác bytes,
  replay giữ reject và history. Đây là logic test, không phải người dùng thật đã chấm.
- Quyết định: mỗi session có workspace ngẫu nhiên, ghi exclusive không đè version cũ;
  ReviewEvent chứa previous_claim/new_claim. Sửa text hạ assessment về insufficient;
  reject/needs_review lan truyền tới recommendation qua premise graph.
- Accept là đánh giá người dùng, không tự đổi evidence assessment thành verified/supported.
- Export JSON chứa snapshots và history; replay kiểm lại hash/locator/IDs/rules,
  hiển thị thời điểm gốc. Markdown dẫn anchor evidence ổn định, text nguồn không chạy HTML.

### D004 Download ghim IP và parser trong worker có deadline
- Thời điểm: 15/10/2026, mốc ingestion.
- Thiết kế trước: yêu cầu kiểm tra SSRF/timeout, chưa có implementation.
- Quan sát: môi trường không có API base/model/key; 11 test ingestion đã PASS,
  gồm PDF 2 trang có chữ, PDF không chữ và các địa chỉ private/metadata.
- Thay đổi: URL kiểm tra tất cả DNS answers, kết nối numeric IP với Host/SNI gốc;
  mỗi redirect được kiểm tra lại. Worker subprocess giới hạn wall clock cả DNS/PDF.
  Tắt proxy từ môi trường và retry download; từ chối response nén để tránh giải nén không giới hạn.
- Vì sao: kiểm tra URL trước một lần không bảo vệ đích thực kết nối. Giữ httpx
  theo ARCHITECTURE/requirements.in, không đổi sang thư viện thay thế theo skill.
- Đánh đổi: nguồn chỉ trả compressed text hoặc không UTF-8 cần bản thay thế;
  giới hạn bộ nhớ cứng của worker chưa có trên Windows, không gọi là sandbox bảo mật.
- Kiểm chứng lại: `uv run pytest tests/unit/test_ingestion.py -q`.
- Kết quả: 11 passed, chưa có live LLM. Không đo lợi ích tốc độ người dùng.

### D005 Hai lượt LLM với kiểm tra độc lập và nhãn chưa chấm ngữ nghĩa
- Thiết kế trước: hai lượt chính và rule checks theo ARCHITECTURE.
- Quan sát: 5 test rules đã PASS, gồm gross/net khác nhau, dimensions unknown,
  chặn recommendation khi xung đột, từ chối fact material không có support.
- Quyết định: evidence chỉ được định vị trong span đã gửi; code tạo offsets/hash;
  JSON sai được thử sửa tối đa một lần/lượt trong ngân sách chung. Không có fallback mẫu.
  Không cho summary thị trường tự do ngoài claims để tránh dữ kiện không gắn evidence.
- Đánh đổi: metadata/phương pháp thiếu hạ nhãn limited; chặn lựa chọn dựa trên premise
  chưa đủ chắc và luôn cho bước bổ sung dữ liệu. Rule checks chưa chứng minh semantic support.
- Provider ban đầu: adapter HTTPS OpenAI Chat Completions, một endpoint/model do env chọn;
  chưa cam kết API tương thích cho provider khác. JSON mode/token parameter cấu hình tường minh.
- API đã đối chiếu: tài liệu chính thức OpenAI Chat Completions/Structured Outputs;
  HTTPX transport + HTTPCore sni_hostname; Streamlit file_uploader/AppTest; pypdf extract-text.
- Kết quả live: BLOCKED thiếu cấu hình. Không phải PASS/FAIL chất lượng model.

### D012 Chuyển endpoint sang Google Gemini theo yêu cầu người dùng
- Thời điểm thật: 15/10/2026 (GMT+7), trước khi có key Gemini.
- Thiết kế trước: một endpoint/model cấu hình qua `.env` (D004–D011).
- Quan sát/log dẫn chứng: Groq free `gpt-oss-20b` giới hạn 8K TPM
  (docs Groq + error message thực tế "Limit 8000, Requested 10210"); payload R02
  ~9–10K tokens/request nên HTTP 413 ổn định; probe ctx=5000 cho HTTP 200.
- Thay đổi: `.env` dùng base `https://generativelanguage.googleapis.com/v1beta/openai`,
  model `gemini-2.5-flash` (sau đó `gemini-2.0-flash` 404 đã retire → user chọn đổi,
  hiện `gemini-2.5-flash-lite` sau khi liệt kê 63 models qua API), key do người dùng
  thêm; cấu hình Groq cũ giữ trong `.env.bak.groq-20261015`. Không sửa code
  (adapter OpenAI-compat dùng chung).
- Vì sao chọn: yêu cầu tường minh của người dùng; Gemini free tier kỳ vọng TPM cao
  hơn Groq free; endpoint OpenAI-compat đã xác nhận trong docs Google.
- Đánh đổi: số TPM free theo model phải xem trong AI Studio, chưa xác minh;
  JSON mode/token param qua compat layer cần probe 1 request thực tế sau khi có key.
- Cách kiểm chứng lại: thêm key → probe 1 request đo status/TPM → chạy evaluator R01/R02.
- Kết quả kiểm chứng: probe 2.5-flash-lite HTTP 200 JSON hợp lệ; R01 ra report live,
  R02 còn BLOCKED output-cap (xem D013 và STATUS).

### D013 Retry một lần cho extraction quote sai và synthesis thiếu premise/ID
- Thời điểm thật: 15/10/2026, sau khi bắt được raw output live chứng minh model
  paraphrase quote (~2/10 lần) và sinh inference thiếu reasoning/dangling IDs.
- Thiết kế trước: citation locate fail hoặc validation fail abort ngay.
- Quan sát/log dẫn chứng: `citation_diagnostic_2.json` (quote paraphrase không tồn tại
  trong nguồn), evaluator runs `2aeca5e9` (inference thiếu premise), `854eb01d`
  (dangling evidence ID), `f7fa169b` (cả hai với flash-lite).
- Thay đổi: `extract_and_locate` sinh lại extraction tối đa 1 lần khi quote không khớp;
  `synthesize_and_validate` sinh lại synthesis tối đa 1 lần khi fail `dangling_id`,
  `missing_support`, `inference`. Vẫn strict, không fuzzy-match, trong ngân sách
  request chung; mỗi retry ghi warning vào coverage. Test đỏ→xanh:
  `test_paraphrased_quote_is_retried_once_and_report_survives`,
  `test_invalid_synthesis_is_retried_once_and_report_survives` + 2 test abort.
- Vì sao chọn: lỗi model ngẫu nhiên, không phải lỗi logic span/validation; retry
  bounded giữ được report mà không hạ chuẩn kiểm tra.
- Đánh đổi: tốn thêm tối đa 2 requests/run; fail lặp lại lần 2 vẫn abort.
- Cách kiểm chứng lại: `uv run pytest tests -q` (59 passed) + evaluator run `8f2a8eb0`
  R01 ra report sau 2 requests không retry.
- Kết quả kiểm chứng: PASS offline; live R01 PASS có điều kiện (1 claim overstated
  đã insufficient), R02 vẫn BLOCKED hạ tầng/output-cap.
- Thời điểm thật: 15/10/2026 (GMT+7), trước khi có key Gemini.
- Thiết kế trước: một endpoint/model cấu hình qua `.env` (D004–D011).
- Quan sát/ca test/log dẫn chứng: Groq free `gpt-oss-20b` giới hạn 8K TPM
  (docs Groq + error message thực tế "Limit 8000, Requested 10210"); payload R02
  ~9–10K tokens/request nên HTTP 413 ổn định; probe ctx=5000 cho HTTP 200.
- Thay đổi: `.env` dùng base `https://generativelanguage.googleapis.com/v1beta/openai`,
  model `gemini-2.5-flash`, key để trống; cấu hình Groq cũ giữ trong
  `.env.bak.groq-20261015`. Không sửa code (adapter OpenAI-compat dùng chung).
- Vì sao chọn: yêu cầu tường minh của người dùng; Gemini free tier kỳ vọng TPM cao
  hơn Groq free; endpoint OpenAI-compat đã xác nhận trong docs Google.
- Đánh đổi: số TPM free theo model phải xem trong AI Studio, chưa xác minh;
  JSON mode/token param qua compat layer cần probe 1 request thực tế sau khi có key.
- Cách kiểm chứng lại: thêm key → probe 1 request đo status/TPM → chạy evaluator R01/R02.
- Kết quả kiểm chứng: NOT_RUN (đang chờ key của người dùng).
- Thời điểm thật:
- Thiết kế trước:
- Quan sát/ca test/log dẫn chứng:
- Thay đổi:
- Vì sao chọn:
- Đánh đổi:
- Cách kiểm chứng lại:
- Kết quả kiểm chứng: NOT_RUN / nội dung quan sát thật

Không điền “đã cải thiện” khi chưa đo; giữ phân biệt giả thuyết và quan sát.

