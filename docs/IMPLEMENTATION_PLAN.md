# Kế hoạch triển khai trong 3 ngày

Đây là checklist công việc, không phải tiến độ đã hoàn thành.
Ngày 1–3 tương đối từ lúc bắt đầu. STATUS ghi thời điểm thật khi thực hiện.

## Ngày 1 Lát cắt đầu tiên
- [ ] Kiểm tra repo, môi trường, hướng dẫn có sẵn; xác định lệnh Python phù hợp.
- [ ] Tạo virtualenv, cài/thử dependency, lưu bản pin thực tế.
- [ ] Tạo contracts và config; validate input, unknown và giới hạn.
- [ ] Đọc text fixture và PDF có lớp chữ; URL public với giới hạn an toàn.
- [ ] Chuẩn hóa nội dung, hash, đoạn và locator.
- [ ] Unit test quote offsets, scope, unknown, nguồn lỗi.
- [ ] Tạo UI nhập câu hỏi, nguồn và xem đoạn gốc.
- [ ] Tích hợp provider adapter thật nếu có key; không cần chờ để làm phần còn lại.
- [ ] Chạy một ca từ input → evidence → claim → mở quote.
**Mốc:** có lát cắt chạy xuyên suốt; nếu live bị chặn, ghi riêng blocker.

## Ngày 2 Chất lượng và tái sử dụng
- [ ] Tách fact/inference, premise IDs, recommendations.
- [ ] Source assessment có lý do và provenance; lineage không đếm trùng.
- [ ] Phân biệt khác scope với mâu thuẫn cùng scope; missing data/abstention.
- [ ] Human review và export report cùng nguồn/phiên bản.
- [ ] Câu hỏi thứ hai và thứ ba đổi nhiệm vụ/thị trường, không hardcode.
- [ ] Chạy bộ dev; tìm lỗi retrieval, số liệu, semantic support; ghi kết quả thật.
- [ ] Chuẩn bị nguồn thị trường thật từ nguồn công khai có quyền sử dụng.
- [ ] Cập nhật decision record cho thay đổi có quan sát cụ thể.
**Mốc:** nhiều câu hỏi sử dụng cùng pipeline và có demo ca khó.

## Ngày 3 Kiểm thử và bàn giao
- [ ] Chạy regression unit/integration; chạy eval reserved và live như EVALUATION.
- [ ] Chấm mọi material claim và kiểm tra bằng chứng bị bỏ sót; không chỉ kiểm tra citation tồn tại.
- [ ] Tìm một ca sản phẩm chưa xử lý tốt thật sự; không cố tạo lỗi để đủ chỉ tiêu.
- [ ] Nếu chưa thấy failure, mở rộng ca thực tế; không gán NOT_RUN thành FAIL.
- [ ] Nếu có người thử, đo thời gian gồm nhập nguồn + đọc + sửa; nếu không, ghi chưa đo.
- [ ] Hoàn thiện README bằng lệnh đã chạy, giới hạn, ví dụ, kết quả, cách local.
- [ ] Chuẩn bị cấu hình deploy, secrets và giới hạn chi phí; chỉ publish khi được yêu cầu.
- [ ] Xác nhận link online từ bên ngoài phiên triển khai nếu đã deploy.
- [ ] Quay video thật ≤5 phút theo DEMO; người dùng trực tiếp thu/duyệt giọng nếu cần.
- [ ] Kiểm tra SUBMISSION; cập nhật STATUS và phản hồi 3 câu bắt buộc trong chat.

## Thứ tự cắt giảm khi thiếu thời gian
Giữ input → source → evidence → claim → user verification, uncertainty và test.
Cắt trang trí, chart, hỗ trợ thêm định dạng, web search, database/backend riêng.
Không cắt khả năng kiểm chứng hoặc thay live bằng kết quả hardcode.

