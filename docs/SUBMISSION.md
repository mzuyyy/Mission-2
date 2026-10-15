# Checklist bàn giao

Trạng thái mới nhất: repo public, file trình bày và bộ ca kiểm thử đã có.
Đã đăng nhập Streamlit; đang chờ chủ tài khoản đăng nhập GitHub và kết nối với
Community Cloud để tạo bản online.
Chưa có video quay thật; chưa nghiệm thu toàn bộ chất lượng ngữ nghĩa.

## Repo public
- [x] README đã chuyển từ hướng dẫn starter sang hướng dẫn app.
- [x] Lệnh cài/chạy/test copy được và đã thực thi.
- [x] Có cấu hình mẫu không có secrets, dependencies pin/lock đã thử.
- [x] Có kiến trúc ngắn, ví dụ câu hỏi, nguồn hỗ trợ và giới hạn.
- [x] Có fixture được đánh dấu, tách khỏi dữ liệu market thật.
- [x] Có test results thật và cách tái hiện, không chỉ case specification.
- [x] Kiểm tra secrets cả working tree và lịch sử trước khi public (phạm vi quét ghi ở STATUS).
- [x] Chỉ public fixture synthetic và ảnh UI synthetic; không publish raw nguồn thật chưa rõ quyền.
- [x] Chỉ tạo repo/push public theo yêu cầu rõ của người dùng.
- [ ] LICENSE do chủ repo lựa chọn, không tự gán quyền cho tài liệu bên thứ ba.

## Bản chạy thử
- [ ] Link online kiểm tra từ phiên ngoài; hoặc lý do cụ thể và local steps đã thử.
- [ ] Secrets server-side, giới hạn nguồn/requests, không cache riêng tư chung phiên.
- [ ] Giới hạn live và fixture/replay hiển thị rõ.
- [ ] Nếu host ephemeral, ghi rõ report không bảo đảm tồn tại lâu, người dùng có thể export.

## Bộ test và video
- [x] ≥5 ca đã chạy có format Kỳ vọng → Thực tế → Đạt/Chưa đạt → Điều học được.
- [x] Có ca tốt/khó trong test logic và failure PDF thật; phân biệt mock với live.
- [x] Hai câu hỏi nguồn thật đã sinh report e1.1 khác nhiệm vụ/phạm vi; chưa đủ human grading.
- [ ] Video thật ≤5 phút, demo kiểm chứng và limitation.
- [x] Có PowerPoint 7 slides và notes dự kiến 4:40 hỗ trợ quay video.
- [x] Blocker hosting/429/semantic grading được ghi cụ thể, không thay bằng “done”.

Tệp: [PowerPoint](../deliverables/Gamota_Mission_2_MVP.pptx),
[bộ ca kiểm thử](SUBMISSION_TEST_CASES.md), [test log và giới hạn](TEST_RESULTS.md),
[deploy](DEPLOYMENT.md).

## Phản hồi chat cho ứng viên
Nêu kết quả và 3 câu bắt buộc ngoài file, dùng quan sát thật.
Không thêm mục trả lời câu hỏi vào file phân tích hoặc tạo file câu trả lời riêng.

