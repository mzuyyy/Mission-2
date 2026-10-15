# Hợp đồng dữ liệu

Dùng Pydantic hoặc schema tương đương, validate trước lưu/hiển thị.
Không để dữ kiện quan trọng chỉ nằm trong đoạn văn tự do ngoài contracts.

## ResearchRequest
request_id; question; country[]; platforms[]; period_start/end (nullable);
decision_goal; alternatives[]; constraints[]; clarified (bool); created_at.
Nếu trường quyết định chưa xác định, trả needs_clarification cùng câu hỏi cụ thể.

## SourceDocument
source_id; display_title; original_url nullable; local_name nullable;
content_hash; normalized_text; retrieved_at; published_at nullable;
data_period nullable; country[]; platforms[]; publisher nullable;
source_kind (original_report/company_disclosure/syndication/opinion/unknown);
original_root_id nullable; root_relation_reason; metadata_provenance;
read_status (ok/partial/failed/unsupported); read_error nullable;
is_synthetic bool; permission_note.
published_at không thay cho kỳ dữ liệu. Không tự gán ngày đo từ ngày đăng.
Unknown source lineage không được tính như nhiều xác nhận độc lập.
App không được tự cấp nhãn nguồn thật chỉ vì fixture mô phỏng một báo cáo gốc.

## SourceAssessment
source_id; claim_or_question_id; origin/methodology/scope/freshness/interest/independence:
mỗi dimension gồm value (yes/no/partial/unknown), rationale và provenance.
provenance là user/document/heuristic/model/human.
summary_label (strong_for_this_claim/limited/unsuitable/unknown).
Đây là đánh giá theo ngữ cảnh, không phải xác suất nguồn đúng.

## Evidence
evidence_id; source_id; content_hash; quote; start_char; end_char;
page_number nullable; section nullable; surrounding_context;
metric nullable; value nullable; unit/currency nullable;
country/platform/period nullable; gross_net nullable; actual_or_estimate nullable.
Value có thể null cho bằng chứng định tính.
Draft extraction nội bộ ở prompt e1.1 có thể chỉ gửi evidence_id/source_id/span_id,
không cần quote. Code lấy nguyên span từ snapshot để tạo Evidence cuối với quote/offsets/hash
bắt buộc như trên; nếu model vẫn gửi quote thì chỉ nhận chuỗi con exact của đúng span.
Không fuzzy-match hoặc dùng văn bản do model sửa làm snapshot.
Offsets theo normalized_text, end exclusive, quote phải khớp chính xác.
Không lấy số lượng nguồn làm metric thị trường.

## Claim
claim_id; text; kind (fact/inference/hypothesis); material (bool);
assessment (supported/limited/conflicting/insufficient);
evidence_links[{evidence_id, relation: supports/contradicts/context}];
premise_claim_ids[]; assumptions[]; missing_data[]; limitations[];
human_review (unreviewed/accept/needs_review/reject).
Fact có material=true cần supports evidence hợp lệ để xuất như dữ kiện có căn cứ.
Inference cần premise IDs có thật và giải thích suy luận. Hypothesis phải hiện là giả thuyết.
Material = có thể đổi lựa chọn/hành động/đánh giá rủi ro.

## Conflict
conflict_id; claim_ids[]; evidence_ids[]; comparison_dimensions;
same_scope (true/false/unknown); explanation; unresolved (bool);
affected_recommendation_ids[].
Unknown comparison dimensions không được ép kết luận là hai nguồn đang mâu thuẫn thật.
Bằng chứng khác metric có thể là căng thẳng kinh doanh nhưng chưa là contradiction của cùng fact.

## Recommendation
recommendation_id; action; rationale; premise_claim_ids[]; conditions[];
blocking_unknowns[]; blocked (bool); next_step; owner_role nullable.
Không tự bịa người chịu trách nhiệm. Không đưa lời khuyên đầu tư chắc chắn khi blocked.
Có thể đề xuất xin dữ liệu/thử nghiệm nhỏ dù chưa chọn được cơ hội.

## ResearchReport
schema_version; report_id; request; source_ids[]; assessments[];
evidence[]; claims[]; conflicts[]; recommendations[]; missing_data[];
coverage{read_sources, failed_sources, partial_sources, context_truncated, omitted_span_ids};
is_synthetic; mode (live/fixture/replay); generated_at;
model_id nullable; prompt_version; source_hashes;
usage{request_count, tokens nullable, estimated_cost nullable, latency_ms};
validation{quote_checks, dangling_ids, failures[]};
review_history[].
Unknown token/cost là null, không phải 0. Chỉ báo cost nếu có rate/config xác thực.
Replay phải hiện “kết quả đã lưu”, không phải lần chạy live mới.
Report lẫn nguồn giả lập thì luôn hiện nhãn có dữ liệu giả lập.

## ReviewEvent
event_id; report_id; claim_id nullable; previous_version; new_version;
decision; note; timestamp.
Human reject không xóa snapshot trước. Version sau phải giữ truy vết chỉnh sửa.

## EvaluationResult
run_id; case_id; split; input_hashes; code_revision; model_id; prompt_version;
actual_output_path; expected; actual; verdict (NOT_RUN/PASS/FAIL/BLOCKED);
learned; timestamp; reviewer; checks; live_or_mock.
Kết quả semantic từ người chấm lưu riêng với check tự động.
Expected labels chỉ evaluator dùng; app không đọc eval/expected.

