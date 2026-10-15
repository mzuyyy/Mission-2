# Bộ tình huống kiểm thử nộp Mission 2

Ngày 15/10/2026. Bộ lệnh bên dưới đã chạy: **28 passed, 0.87s**;
browser Chromium thật: **1 passed, 10.55s**. Đây là kiểm thử logic bằng nguồn
synthetic/mock và replay. Hai ca nguồn thị trường thật được ghi riêng bên dưới;
không coi 28 test offline là 28 nghiên cứu live AI.

## Các ca logic có thể chạy lại

| ID | Tình huống | Kỳ vọng | Kết quả thực tế | Đạt/Chưa đạt | Điều học được |
| --- | --- | --- | --- | --- | --- |
| S01 | Câu hỏi và nguồn khác nhiệm vụ | Cùng pipeline, không rò đáp án câu trước | Hai test pipeline khác câu hỏi/nguồn PASS; quote và nội dung theo nguồn mock mới | Đạt logic, chưa chứng minh live | Tách pipeline khỏi UI giúp thử nhiệm vụ khác bằng cùng code |
| S02 | Không biết giá trị và kỳ đo | Unknown giữ null; ngày đăng không thay kỳ đo | Hai test unknown/measurement-period PASS | Đạt logic | Không đủ số liệu phải hiện thiếu dữ liệu |
| S03 | Gross và net khác nhau | Không gọi là mâu thuẫn cùng chỉ số | Test gross/net PASS; same_scope=false | Đạt logic | Phải so dimensions trước khi so giá trị |
| S04 | Cùng phạm vi nhưng số trái nhau | Hiện conflict và chặn recommendation | Test same-scope conflict PASS | Đạt logic với draft mock | Citation có thật vẫn cần xử lý xung đột |
| S05 | Quote do model bịa | Từ chối trước synthesis sau retry có giới hạn | Test nonexistent quote PASS; pipeline abort, không có report mẫu | Đạt xử lý lỗi mock | Không sửa quote bằng fuzzy match để vượt kiểm tra |
| S06 | PDF nhiều cột, thứ tự lệnh vẽ khác vị trí | Giữ đúng hàng/cột, không tách nhãn khỏi số | 5 regression PDF/HTML PASS; 3 test đầu từng FAIL trước sửa | Đạt parser, chưa chứng minh model | Plain text có thể làm sai quan hệ số và nhãn |
| S07 | Nguồn dài, phản chứng ở xa | Ghi omission khi context không chứa hết | Test far-counterevidence PASS, coverage báo thiếu | Đạt minh bạch coverage | Không thể suy completeness từ quote match |
| S08 | Người dùng mở bằng chứng, review, export | Quote đúng locator; review tạo phiên bản mới | Browser thật PASS ở 375/768/1280; review v2 và tải JSON | Đạt UI, synthetic replay | Người đọc kiểm tra được nhưng vẫn phải chấm ý nghĩa |

Các test chính:

- S01: `test_two_questions_share_pipeline_and_retain_source_quotes`,
  `test_different_task_uses_new_source_and_no_question_keyword_branch`.
- S02: `test_unknown_value_is_not_zero`,
  `test_source_post_date_cannot_replace_measurement_period`.
- S03/S04: `test_gross_net_difference_is_not_same_scope_conflict`,
  `test_same_scope_conflict_blocks_recommendation`.
- S05: `test_nonexistent_quote_aborts_before_synthesis`.
- S06: `tests/unit/test_pdf_layout.py`.
- S07: `test_retrieval_exposes_far_counterevidence_omission`.
- S08: `test_browser_offline_replay_review_and_responsive`.

## Ca thị trường thật và failure thật

| ID | Kỳ vọng | Kết quả thực tế | Đạt/Chưa đạt | Điều học được |
| --- | --- | --- | --- | --- |
| R01: VNG HTML, e1.1 | Tách dữ liệu công ty với nhu cầu game tại VN | Run `fa5bafbbe8004b5b8509274e1a56d59e`: CLI exit 0, 5 claims, 5 evidence, quote 5/5, 4 requests | Chạy được; chưa có human semantic/completeness grading | Quote validity không phải semantic support |
| R02: Sea PDF, e1.1 | Đúng cột/kỳ; không dùng số toàn cầu làm số Thái Lan | Cùng run: quote 6/6 nhưng agent audit phát hiện ít nhất 2 claims gán sai Bookings/cột/kỳ | Chưa đạt chất lượng; failure thật | Source text plain mất vị trí; cần giữ layout và người kiểm tra |
| R01/R02 sau sửa, e1.2 | Chạy lại để xem lỗi số đã hết chưa | `24e3d68b0c3745b58ee1abb8528e0d05`: HTTP 429, CLI exit 2, 4/2 requests; R02 thử lại `e91bc1ec57d241fc8814855b5281e6d0` vẫn 429/2 requests | BLOCKED, chưa chấm được | Không gán PASS cho bản sửa chỉ dựa vào unit test |

R02 là failure của sản phẩm quan sát trên nguồn thật; S05 là test lỗi được mô phỏng
để kiểm validator, không thay thế failure đó. Reviewer ngữ nghĩa hiện là trợ lý đối
chiếu nguồn, chưa phải người chấm độc lập. Chưa có baseline người dùng hoặc số đo
tăng tốc. Raw nguồn/logs ở thư mục ignored; bản công khai đã lược bỏ nội dung nguồn.

## Lệnh tái hiện

```powershell
uv sync --frozen
uv run pytest tests/unit/test_rules.py tests/unit/test_integrity.py tests/unit/test_pdf_layout.py tests/integration/test_pipeline.py -q --junitxml=eval/runs/submission_scenarios.xml
uv run playwright install chromium
uv run pytest tests/browser -m browser -q --junitxml=eval/runs/submission_browser.xml
uv run pytest tests -q
uv run python eval/run_evaluation.py --cases eval/real_cases.json --split real
```

Lệnh live cuối cần cấu hình Gemini và quota còn khả dụng; không dùng sudo.
Lệnh evaluator exit 0 chỉ là lưu được kết quả; phải đọc verdict và CLI exit code.
