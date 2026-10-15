# Thiết kế gốc và phạm vi đã chọn

Tóm tắt từ bản Mission 1 đã chốt ngày 07/10/2026, không phải kết quả phỏng vấn người dùng.

## Vấn đề và người dùng
Nhân viên nghiên cứu thị trường hoặc phát triển kinh doanh cần chuẩn bị đề xuất sàng lọc cơ hội
cho người phụ trách phát hành. Kết quả gồm cơ hội nên khảo sát sâu, lý do,
phản chứng, dữ liệu còn thiếu và bước tiếp theo. Không tự quyết định ký phát hành.

## Thiết kế gốc
- Chốt câu hỏi, quốc gia, nền tảng, thời kỳ, mục tiêu và ràng buộc.
- Lập kế hoạch bằng chứng; thu thập/chuẩn hóa; gom nguồn dẫn lại.
- Phân biệt dữ kiện, suy luận và giả thuyết.
- Khuyến nghị có điều kiện, có phản chứng và mức độ chắc chắn.
- Người dùng mở nguồn, sửa/bác bỏ/duyệt; giữ phiên bản.
- Mâu thuẫn chưa giải quyết có thể khiến hệ thống dừng khuyến nghị.
- Dùng một LLM với bộ kiểm tra quy tắc; không cần nhiều agent hoặc fine-tune.

## Phạm vi đầu tiên
Một tình huống sàng lọc tại một thị trường cho mỗi lượt, 2–3 phương án nếu người dùng muốn so sánh.
Nguồn do người dùng cung cấp trước; chưa tìm web tự động diện rộng.
Bản thân ứng dụng phải tiếp nhận câu hỏi và nguồn mới, không khóa cứng một thị trường hay thể loại.

## Mục tiêu kiểm chứng ban đầu
Tỷ lệ nhận định được chứng minh ≥95%, nhận định ảnh hưởng lựa chọn 100%;
giảm thời gian trung vị ≥30% so quy trình hiện tại;
≥80% phiên thử có hành động tiếp theo rõ.
Các tỷ lệ này là mục tiêu, chưa đo được và không phải cam kết chất lượng.
Mẫu nhỏ phải báo tử số/mẫu số, lỗi thực tế và giới hạn.
Không có đánh giá người dùng thì không tuyên bố đã đạt mục tiêu tốc độ.

## Thay đổi đã chốt cho bản triển khai
Python + Streamlit, URL có văn bản/PDF có lớp chữ, kho bằng chứng JSON.
Đây là quyết định thiết kế trước khi code, chưa phải bài học từ thực nghiệm.

