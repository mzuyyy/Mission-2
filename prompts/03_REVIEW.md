Review và sửa MVP theo docs/ACCEPTANCE.md, không chỉ kiểm tra UI chạy.

Đọc AGENTS, PRODUCT_SPEC, DATA_CONTRACTS, EVALUATION, code và test results hiện tại.
Tập trung:
- Fact material có đoạn nguồn thật sự hỗ trợ hay chỉ citation hợp lệ?
- Inference có premises/assumptions và nguồn phù hợp scope?
- Có nhân đôi bài dẫn cùng gốc, lẫn kỳ dữ liệu/ngày đăng, lẫn metric/gross-net?
- Missing data/mâu thuẫn có làm thay đổi/chặn khuyến nghị?
- Có hardcode đáp án, đọc eval/expected trong pipeline hoặc dùng mock không gắn nhãn?
- URL/file limits, SSRF/redirect, secrets, cache theo session và request budget gồm retry?
- App, CLI và eval có gọi cùng core pipeline không?

Ưu tiên sửa lỗi ảnh hưởng lựa chọn trước trang trí.
Mỗi finding cần đường dẫn code, tình huống tái hiện và tác động.
Chạy regression sau sửa. Nếu chưa có key/live output, ghi giới hạn review.
Không xóa test/giảm kỳ vọng để làm xanh; nếu kỳ vọng sai, giải thích và giữ lịch sử.
Cập nhật STATUS và decision records, báo còn gì chưa chứng minh được.

