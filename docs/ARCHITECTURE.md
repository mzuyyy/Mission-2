# Kiến trúc và ranh giới triển khai

## Stack
Python 3.11+, Streamlit; httpx cho tải nguồn, BeautifulSoup cho HTML,
pypdf cho PDF có lớp chữ, Pydantic cho contracts, pytest cho logic.
Một model qua provider adapter cấu hình. Xác nhận SDK/API hiện tại trước khi code.
requirements.in là gợi ý phụ thuộc; tạo pin/lock sau khi cài và thử thành công.
Không mặc định các provider có cùng API structured output hoặc tham số.

## Cấu trúc code Codex cần hiện thực hóa
- app.py: điểm vào Streamlit.
- src/gamota_research/config.py: cấu hình và giới hạn.
- models.py: contract Python theo docs/DATA_CONTRACTS.md.
- ingestion/: public_url.py, pdf.py, normalize.py.
- retrieval.py: chọn đoạn liên quan có giữ phản chứng/coverage.
- sources.py: metadata, đánh giá có lý do, nhóm nguồn.
- llm.py: adapter thật, timeout/retry, output validation.
- pipeline.py: các bước độc lập UI; không đọc eval/expected.
- validation.py: quote/IDs/scope và rule checks.
- storage.py: workspace theo session, version/export.
- cli.py: chạy cùng pipeline cho eval và tái hiện.
- tests/unit/, tests/integration/: kiểm thử code, không gọi live mặc định.
- eval/: input, kỳ vọng riêng, log và đánh giá live.
Không cần tạo package/module không có trách nhiệm cụ thể.

## Pipeline
1. UI lấy scope, hiển thị chỗ mơ hồ; người dùng chốt.
2. Ingestion kiểm tra và đọc nguồn; tạo nội dung chuẩn hóa + hash + locator.
3. Retrieval chọn đoạn; ghi rõ phần không đọc/không chọn/cắt. Không drop phản chứng để fit context.
4. LLM trích evidence/nhận định nháp từ các đoạn, không biết expected test labels.
5. Code xác minh quote và IDs; dấu chưa đủ metadata giữ unknown.
6. LLM tổng hợp từ evidence hợp lệ; fact → evidence, inference → premises.
7. Rule validation lọc citations lỗi, phát hiện comparability và chặn output không hợp lệ.
8. UI hiển thị kết quả + coverage + review; lưu report và user edits thành phiên bản.
Cần mặc định 2 lượt LLM chính, tối đa tổng request theo config gồm retries/repair.
Không thêm self-critic LLM nếu chưa chứng minh cần thiết.

## Retrieval quy mô nhỏ
Bắt đầu lexical ranking có chuẩn hóa tiếng Việt + từ khóa câu hỏi/scope.
Giữ nhiều đoạn từ các nguồn khác nhau, gồm đoạn phản bác tiềm năng.
Ngân sách context là giới hạn, không phải lý do để giả vờ đã đọc toàn bộ.
Log selected span IDs và số ký tự; nếu truncation có thể làm thiếu bằng chứng quyết định,
hạ assessment/abstain. Sau baseline mới cân nhắc embedding nếu có lỗi retrieval quan sát được.

## Citation
Normalize NFC và line endings một lần, giữ normalized_text bất biến theo content hash.
Locator dùng chỉ số ký tự Python của normalized_text: start inclusive/end exclusive.
Kiểm tra normalized_text[start:end] == quote. Lưu normalized_text hoặc snapshot được phép.
Nếu chỉ có quote, code định vị để tạo offsets; không tin offsets model đưa.
Thêm page_index 1-based cho PDF và section/heading nếu tìm được.
Đây chỉ là kiểm tra trích dẫn, không phải chứng minh semantic support.
Không xóa câu lỗi rồi vẫn tuyên bố report hoàn chỉnh; ghi validation failure/coverage.

## Source assessment
Lưu từng dimension: origin, methodology, scope match, freshness, conflicts of interest,
lineage/independence; kèm lý do và provenance.
Nhóm nguồn theo canonical origin đã kiểm tra hoặc declared root ở fixture.
Không tự coi hai domain độc lập hoặc tạo trusted-domain allowlist như chân lý.
Đối chiếu country/platform/period/metric/unit/currency/gross_net/actual_estimate trước khi so số.

## Vận hành
Timeout, cap bytes/pages/sources/context/requests; retry có backoff trong cùng ngân sách.
URL chặn scheme ngoài http(s), private/loopback/link-local/metadata, kiểm tra redirect và DNS.
Download streaming giới hạn, không chạy JS hoặc lệnh từ tài liệu.
Bảo vệ SSRF phải kiểm tra cả đích thực kết nối; không chỉ validate chuỗi URL ban đầu.
Cache nguồn công khai theo hash; dữ liệu user theo session, không cache chung raw report.
Secrets chỉ server-side; không log authorization hoặc nội dung riêng tư.
Chỉ nên public demo với dữ liệu công khai và quota request đủ chặt.

## Tài liệu chính thức để đối chiếu khi triển khai
- https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- https://pypdf.readthedocs.io/en/stable/user/extract-text.html
pypdf không thay OCR; bảng phức tạp cần kiểm thử bằng chính nguồn dùng trong demo.

