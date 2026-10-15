# Đặc tả MVP

## Giả thuyết
Một đề xuất nối được với bằng chứng và nêu rõ bất định giúp người nghiên cứu kiểm tra
căn cứ nhanh hơn mà không tăng lỗi trọng yếu.
MVP kiểm tra tính khả thi của luồng; đo lợi ích tốc độ cần thử người dùng riêng.

## Người dùng và nhiệm vụ
Người nghiên cứu/BD chuẩn bị phương án cho người phụ trách phát hành.
Ứng dụng hỗ trợ sàng lọc và xác định bước khảo sát, không thay người chịu trách nhiệm quyết định.

## Input
- Câu hỏi tự do bằng tiếng Việt.
- Quốc gia; nền tảng; thời kỳ dữ liệu hoặc ghi rõ chưa xác định.
- Mục tiêu: nhu cầu, kiếm tiền, cạnh tranh, so sánh cơ hội hoặc kiểm tra nhận định.
- Các phương án nếu so sánh; trường này không bắt buộc cho câu hỏi khác.
- URL công khai có văn bản và PDF có lớp chữ, tổng tối đa theo cấu hình.
- Có thể bổ sung metadata nguồn; giữ xuất xứ user/model/unknown.
Nếu hỏi “tiềm năng” nhưng thiếu tiêu chí, hỏi một câu làm rõ có lựa chọn; không tự đoán lợi nhuận.

## Output
1. Tóm tắt trả lời trực tiếp trong phạm vi đã chốt.
2. Danh sách nhận định, phân biệt fact/inference/hypothesis.
3. Evidence liên quan đến từng nhận định: đoạn trích, nguồn, vị trí, kỳ đo, hạn chế.
4. Đánh giá nguồn theo câu hỏi với lý do và unknown rõ ràng.
5. Mâu thuẫn/khác phạm vi và ảnh hưởng tới kết luận.
6. Missing data và hành động tiếp theo.
7. Cảnh báo coverage: nguồn lỗi, cắt bớt, không đọc được, metadata chưa biết.
8. Người dùng đánh dấu accept/needs_review/reject, thêm ghi chú; lưu bản trước/sau.

## Luồng UI
Một màn hình với vùng nhập câu hỏi/nguồn và các tab:
- Kết quả: nhận định, hành động có điều kiện, điểm chưa biết.
- Bằng chứng: chọn một nhận định để thấy đúng đoạn nguồn và ngữ cảnh.
- Nguồn: metadata, hạn chế, nhóm gốc, trạng thái đọc và chất lượng đối với nhận định.
- Kiểm tra: ghi chú và đánh dấu của người dùng.
UI tiếng Việt, không cho điểm tin cậy giả. Xuất JSON và Markdown kèm citations ổn định.
Không cần export PDF trong 3 ngày.

## Ba loại câu hỏi để chứng minh tái sử dụng
A. So sánh idle RPG và puzzle tại một quốc gia với tiêu chí do người dùng chốt.
B. Phân tích cạnh tranh/phát hành ở một quốc gia khác.
C. Kiểm tra một nhận định tăng trưởng khi chỉ số khác chiều.
Đây là ví dụ; pipeline không branch theo nguyên văn câu hỏi.
Ít nhất hai ca live thị trường thật phải khác nhiệm vụ/phạm vi, không chỉ diễn đạt lại.

## Trạng thái bằng chứng
- supported: có bằng chứng phù hợp hỗ trợ nhận định; chưa đồng nghĩa được chuyên viên xác minh.
- limited: có bằng chứng nhưng thiếu phạm vi, phương pháp hoặc độ bao phủ.
- conflicting: bằng chứng cùng phạm vi trái nhau chưa giải quyết.
- insufficient: thiếu bằng chứng quyết định.
Tách khỏi human_review = unreviewed/accept/needs_review/reject.
Không dùng nhãn “đã xác minh” cho output chỉ qua LLM.

## Không làm
Web search diện rộng, nguồn trả phí cần bypass, OCR đầy đủ, nhận dạng chart,
dự báo doanh thu, fine-tune, multi-agent, vector DB, account system, realtime dashboard.
Nguồn scan/khóa truy cập: cảnh báo và đề nghị tài liệu thay thế.

## UX khi lỗi
Thiếu key: cho xem nguồn/fixture, vô hiệu hóa sinh live, hướng dẫn cấu hình tại máy.
URL lỗi: liệt kê nguồn bị lỗi, tiếp tục nguồn còn đọc được nếu đủ; nêu giới hạn.
Không có bằng chứng: báo insufficient và yêu cầu cụ thể dữ liệu cần thêm.
Model lỗi JSON: sửa có giới hạn; thất bại thì hiển thị lỗi, không dựng kết quả mẫu.

