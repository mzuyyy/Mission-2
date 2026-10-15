from gamota_research.contracts import Evidence, SourceDocument
from gamota_research.errors import ResearchError
from gamota_research.ingestion.normalize import text_hash
from gamota_research.models import EvidenceDraft, Span


def locate_evidence(
    draft: EvidenceDraft, spans: list[Span], sources: list[SourceDocument]
) -> Evidence:
    span = next(
        (s for s in spans if s.span_id == draft.span_id and s.source_id == draft.source_id), None
    )
    source = next((s for s in sources if s.source_id == draft.source_id), None)
    if not span or not source:
        raise ResearchError("citation", f"{draft.evidence_id}: span/source không hợp lệ.")
    quote = draft.quote if draft.quote is not None else span.text
    offset = span.text.find(quote)
    if offset < 0:
        raise ResearchError("citation", f"{draft.evidence_id}: quote không khớp span đã chọn.")
    if span.text.find(quote, offset + 1) >= 0:
        raise ResearchError("citation", f"{draft.evidence_id}: quote lặp; cần trích đoạn dài hơn.")
    start = span.start_char + offset
    end = start + len(quote)
    result = Evidence(
        **draft.model_dump(exclude={"span_id", "quote"}),
        quote=quote,
        content_hash=source.content_hash,
        start_char=start,
        end_char=end,
        page_number=span.page_number,
        surrounding_context=source.normalized_text[max(0, start - 250) : end + 250],
    )
    check_evidence(result, source)
    return result


def check_evidence(evidence: Evidence, source: SourceDocument) -> None:
    valid = (
        evidence.source_id == source.source_id
        and evidence.content_hash == source.content_hash == text_hash(source.normalized_text)
        and 0 <= evidence.start_char < evidence.end_char <= len(source.normalized_text)
        and source.normalized_text[evidence.start_char : evidence.end_char] == evidence.quote
    )
    if evidence.page_number is not None:
        valid = valid and any(
            p.page_number == evidence.page_number
            and p.start_char <= evidence.start_char < evidence.end_char <= p.end_char
            for p in source.pages
        )
    if not valid:
        raise ResearchError("citation", f"{evidence.evidence_id}: hash/quote/locator không hợp lệ.")
