# Điều kiện nghiệm thu

## Tối thiểu để gọi là MVP chạy được
- [ ] Cài và chạy từ README trong môi trường sạch đã thử.
- [ ] Ít nhất hai câu hỏi khác mục tiêu/phạm vi chạy cùng pipeline với live LLM.
- [ ] URL công khai/PDF có lớp chữ đọc được; lỗi nguồn được nêu.
- [ ] Bấm nhận định mở đúng quote + nguồn + locator + ngữ cảnh.
- [ ] Tất cả fact material có evidence hỗ trợ, kiểm tra bằng người chấm trong tập eval.
- [ ] Inference có premise và giả định; unknown không đổi thành 0.
- [ ] Đánh giá nguồn có lý do theo nhận định, phân biệt nguồn dẫn lại và gốc.
- [ ] Có mâu thuẫn/thiếu dữ liệu được hiện rõ và chặn lời khuyên bị ảnh hưởng.
- [ ] Có human review và export giữ phiên bản.
- [ ] UI live/fixture/replay khác nhau rõ; không có đáp án hardcode trong pipeline.

## Kiểm thử và bằng chứng bàn giao
- [ ] Unit test kiểm tra rule/locator/error handling; không thay thế live eval.
- [ ] ≥5 ca end-to-end chạy thật với actual output + model/prompt/source hashes.
- [ ] Có ca tốt, ca khó, ca failure thực sự; biết phân biệt lỗi sản phẩm với lỗi kỳ vọng.
- [ ] Ít nhất hai ca dùng nguồn thị trường thật đã đọc và có đủ metadata.
- [ ] Có kiểm thử câu hỏi mới; nói rõ mẫu nhỏ, chưa đo khả năng tổng quát rộng.
- [ ] Kết quả NOT_RUN/BLOCKED không tính PASS và không tự tính FAIL sản phẩm.
- [ ] Báo support tỷ lệ tử số/mẫu số, unsupported material count và missed conflicts.
- [ ] Chưa thử người dùng thì không công bố giảm thời gian hoặc tăng quyết định đúng.

## Đủ điều kiện nộp
- [ ] Repo public và README thật (không còn README starter làm hướng dẫn duy nhất).
- [ ] Không secrets, dữ liệu riêng tư hoặc báo cáo có bản quyền không được phân phối.
- [ ] Link online chạy được hoặc lý do chưa deploy + local steps đã thử.
- [ ] Video demo thật ≤5 phút và bộ test có đúng format của đề.
- [ ] 3 câu bắt buộc trả trong chat dựa kết quả thật, không nhúng vào file phân tích.

