Bạn hãy triển khai MVP Gamota Mission 2 trong repo hiện tại.

Đọc AGENTS.md, README.md, docs/MISSION_2.md, docs/MISSION_1_BASELINE.md,
docs/PRODUCT_SPEC.md, docs/ARCHITECTURE.md, docs/DATA_CONTRACTS.md,
docs/IMPLEMENTATION_PLAN.md, docs/ACCEPTANCE.md, docs/EVALUATION.md và STATUS.md.
Kiểm tra code/hướng dẫn đã có trước khi sửa; bảo toàn thay đổi người dùng.

Mục tiêu: câu hỏi có phạm vi + nguồn URL/PDF do người dùng cung cấp →
bằng chứng có locator → nhận định có căn cứ, phản chứng và missing data →
người dùng bấm mở đúng đoạn nguồn và ghi nhận review.
Dùng Python + Streamlit, một LLM cấu hình được, kho JSON. Không hardcode câu trả lời
theo case ID/câu hỏi. Chưa làm search diện rộng, nhiều agent, fine-tune hoặc vector DB.

Hãy lập kế hoạch ngắn rồi bắt đầu viết code, không chỉ đề xuất.
Ưu tiên một lát cắt chạy xuyên suốt trước:
contracts → ingestion/quote locator → UI → provider thật → claim/evidence →
uncertainty/source assessment → review/export → eval.
Tách core khỏi UI để CLI và test gọi cùng pipeline.

Fixture trong data/fixtures là dữ liệu giả lập phải gắn nhãn.
eval/expected chỉ dành cho evaluator, không nạp vào LLM/pipeline.
Thiếu API key thì vẫn hoàn thành phần offline, chỉ rõ live đang BLOCKED;
không thay model bằng đáp án mẫu rồi báo đã chạy.
Đọc tài liệu API chính thức trước khi tích hợp. Tự quyết định chi tiết nhỏ, hỏi khi bị chặn
bởi cấu hình cần người dùng cung cấp; không yêu cầu gửi key trong chat.

Chạy test phù hợp và sửa lỗi; lưu actual output, model/prompt/source hashes cho ca live.
Cần ít nhất 5 ca end-to-end, nhiều câu hỏi, ca tốt, ca khó và một failure quan sát thật.
Không điền báo cáo như thể đã chạy khi mới có mock/unit tests.
Nếu có người thử mới báo số liệu thời gian; không bịa mức cải thiện.

Cập nhật STATUS và DECISIONS sau mỗi mốc. Chỉ chuẩn bị deploy/repo public,
chưa xuất bản ra ngoài trong lượt này.
Kết thúc bằng cách chạy app/test đã kiểm tra, phần đã xong, lỗi/blocker,
file quan trọng và bước tiếp theo. Trả lời 3 câu bắt buộc trong chat khi có bằng chứng thật;
không thêm câu trả lời vào tài liệu phân tích hoặc tạo file trả lời riêng.

