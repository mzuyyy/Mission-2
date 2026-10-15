# Giao diện nghiên cứu

Tiếng Việt; ưu tiên đọc, kiểm chứng và trạng thái chưa biết. Dùng thành phần Streamlit
native, không thêm frontend framework. Tham chiếu minimalist của omo:frontend;
giữ mật độ phù hợp công cụ nghiên cứu, không dùng hero hay animation trang trí.

## Tokens
- Primary/action: #176B53; background: #FFFFFF; secondary surface: #F4F6F5;
  body: #182521. Trạng thái dùng st.info/warning/error native, kèm nhãn chữ.
- Font: sans-serif hệ thống của Streamlit, hỗ trợ dấu tiếng Việt.
- Type scale và spacing: native Streamlit; không override CSS kích thước.
- Depth: native containers có border; không shadow tự tạo.

## Thành phần
1. Form câu hỏi/phạm vi với nhãn đầy đủ, một nguồn mỗi dòng.
2. Bốn tab Kết quả / Bằng chứng / Nguồn / Kiểm tra.
3. Claim selectbox và nút Mở bằng chứng: chọn claim, mở quote bằng st.code,
   hiển thị offsets/hash/ngữ cảnh dưới quote. Source text luôn là text thuần.
4. Warning/caption riêng cho fixture, replay, coverage và live bị chặn.
5. Review form có accept/needs_review/reject, lưu phiên bản; export kèm snapshot.

## Responsive và an toàn hiển thị
Một cột nội dung, không HTML không tin cậy, không markdown do model tạo.
Không hiển thị secret hoặc raw provider error. Link nguồn chỉ http(s).
Empty, disabled, error giữ hướng dẫn hành động cụ thể.
