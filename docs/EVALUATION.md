# Đánh giá chất lượng

## Hai lớp kiểm thử
1. Unit/integration bằng fixture và mock: kiểm tra parser, contracts, quote, IDs,
   scope, lineage, budget, lỗi provider. Không tuyên bố đây là nghiên cứu do live AI thực hiện.
2. End-to-end live: cùng pipeline UI/CLI, nguồn đã chuẩn bị, LLM thật, lưu output rồi chấm.
   Fixture live đánh giá logic; cần thêm nguồn thị trường thật để chứng minh giá trị miền.

## Dữ liệu và chống rò đáp án
eval/cases.json chỉ chứa input. eval/expected chứa kỳ vọng cho evaluator.
Không nạp expected vào LLM, không branch theo case ID hoặc question text để trả lời mẫu.
split=dev được dùng để tìm lỗi; split=reserved chỉ chạy sau khi chốt prompt.
Reserved là tập hồi quy giữ lại trong pack này, không phải benchmark độc lập lớn.
Nếu đã xem kết quả rồi sửa để tối ưu, ghi việc đó và thêm ca mới trước khi nói “chưa thấy trước”.

## Chuẩn bị ca thật
Điền eval/real_cases_template.json: URL thật, snapshot/hash nếu có quyền,
kỳ dữ liệu, scope và đoạn gold do người đọc xác nhận.
Dùng ít nhất hai câu khác nhiệm vụ/thị trường; không chỉ viết lại một câu.
Khi chỉ có một nguồn hoặc không đủ dữ liệu, kỳ vọng có thể là limited/insufficient.
Không tự chọn “nguồn đáng tin” chỉ vì đúng hướng muốn kết luận.
Không tải về/commit tài liệu không được phân phối; lưu URL và trích đoạn phù hợp.

## Quy trình mỗi ca
1. Đóng băng input, kỳ vọng và source hashes trước khi chạy.
2. Ghi revision, provider/model, prompt version, tham số generation, thời điểm.
3. Chạy app/CLI thật; lưu request và report raw để tái hiện.
4. Chấm locator tự động; người chấm đọc ngữ cảnh cho semantic support và completeness.
5. Ghi: Kỳ vọng → Kết quả thực tế → Đạt/Chưa đạt → Điều học được.
6. FAIL cần dẫn output cụ thể; BLOCKED cần nguyên nhân; NOT_RUN giữ trống actual/learned.
7. Ca bất định được từ chối đúng có thể PASS. Không mặc định abstention là failure.

## Rubric
- Citation validity: số quote khớp nguồn / tổng quote; IDs tồn tại, đúng source hash.
- Material factual support: số fact material có evidence thật sự hỗ trợ /
  tổng fact material. Ghi cả số tuyệt đối.
- Unsupported material claims: đếm riêng, mục tiêu bằng 0 trong tập được chấm.
- Scope correctness: không trộn chỉ số, quốc gia, nền tảng, thời kỳ hoặc gross/net.
- Source differentiation: lý do đánh giá đúng và không nhân đôi gốc.
- Conflicts/missing data: phát hiện các mục gold quan trọng và nêu ảnh hưởng.
- Action usefulness: bước tiếp theo cụ thể, phù hợp mức bằng chứng; người chấm giải thích.
- Completeness: có bỏ sót phản chứng hoặc caveat quyết định không?
Không dùng citation accuracy một mình để kết luận report đáng tin.

## Cách gọi một ca PASS
Tất cả kỳ vọng trọng yếu của ca đạt; không có unsupported material claim;
hành vi từ chối/cảnh báo đúng với dữ liệu.
Nếu model không sinh fact vì insufficient, mẫu số support có thể bằng 0:
ghi N/A, không gán 100%; vẫn chấm abstention và missing data.
Test mock chỉ chứng minh code xử lý output đó, không chứng minh model có khả năng tạo nó.

## Lặp và baseline
Chạy ca live nhiều lần nếu ngân sách cho phép, ghi variation; mục tiêu 3 lần/ca,
nếu ít hơn nói rõ số lần. Test mới không đạt không xóa khỏi báo cáo.
So baseline cùng câu hỏi/nguồn bằng cách đọc thủ công hoặc chatbot thông thường nếu có thời gian.
Đo toàn bộ thời gian nhập nguồn + đọc + xác minh + sửa; không chỉ thời gian sinh.
Không có người thử hoặc thiếu baseline thì ghi chưa đo hypothesis tốc độ.

## Ca thất bại bắt buộc
Tìm trong tình huống thật: bảng PDF, ngôn ngữ địa phương, nguồn dài,
phản chứng nằm xa, định nghĩa chỉ số không rõ hoặc question ngoài coverage.
Một parser từ chối scan đúng có thể PASS cảnh báo nhưng vẫn là giới hạn chức năng.
Để nộp ca failure, chỉ rõ yêu cầu nghiên cứu nào MVP chưa đáp ứng và kết quả thực tế.
Không cố ý làm sai output, đổi kỳ vọng sau chạy hoặc fake một failure.

## Nơi lưu
Actual run artifacts mặc định ignored ở eval/runs/; chỉ công khai bản đã kiểm tra quyền và redaction.
Tạo docs/TEST_RESULTS.md sau khi chạy thật, không copy các PASS tưởng tượng từ template.
Raw LLM logs không được chứa key hay dữ liệu nhạy cảm.

