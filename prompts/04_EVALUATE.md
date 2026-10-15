Chạy và ghi đánh giá thật cho MVP theo docs/EVALUATION.md.

Xác minh có app/CLI chạy được, môi trường và model/provider.
Nếu chưa sẵn sàng, làm phần chuẩn bị/test offline có ích và báo BLOCKED, không giả kết quả.
Dùng eval/cases.json làm input; expected chỉ evaluator đọc.
Không sửa prompt dựa reserved rồi vẫn gọi reserved là tập chưa thấy.

Tuyển chọn/đọc nguồn market thật và hoàn thiện ít nhất hai ca khác nhiệm vụ/phạm vi
từ eval/real_cases_template.json; không dùng dữ liệu fixture để tuyên bố xu hướng thật.
Chạy ≥5 ca end-to-end; giữ raw output được phép, input hashes, prompt/model/revision.
Chấm citation validity riêng semantic support, scope, independence, completeness và actionability.
Tìm một failure thực tế, phân biệt cảnh báo/từ chối đúng với lỗi đáp ứng nhiệm vụ.
Ghi đúng Kỳ vọng → Kết quả thực tế → Đạt/Chưa đạt → Điều học được.

Sau khi chạy mới tạo docs/TEST_RESULTS.md; giữ NOT_RUN/BLOCKED rõ.
Chỉ xuất bản log đã kiểm tra secrets/quyền sử dụng. Không bịa người đánh giá hay đo thời gian.
Nếu có thể, chạy lặp để đo biến động và nêu sample size.
Cập nhật STATUS, lỗi ưu tiên, thay đổi có bằng chứng. Ba câu bắt buộc trả trong chat,
không thêm vào báo cáo phân tích.

