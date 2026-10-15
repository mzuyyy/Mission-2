import json

from pydantic import JsonValue

from gamota_research.citations import locate_evidence
from gamota_research.config import Settings
from gamota_research.contracts import Evidence, ResearchRequest, SourceDocument
from gamota_research.errors import ResearchError
from gamota_research.ingestion.normalize import text_hash
from gamota_research.llm import Generator
from gamota_research.models import (
    Coverage,
    Extraction,
    ReportBundle,
    ResearchReport,
    Span,
    Synthesis,
    ValidationResult,
)
from gamota_research.prompts import EXTRACTION, PROMPT_VERSION, SYNTHESIS
from gamota_research.retrieval import retrieve
from gamota_research.sources import assess_source, group_sources
from gamota_research.validation import unique_ids, validate_synthesis


def extract_and_locate(
    generator: Generator,
    payload: str,
    spans: list[Span],
    sources: list[SourceDocument],
) -> tuple[Extraction, list[Evidence], bool]:
    """Extract then locator-check quotes.

    One bounded re-extraction when a quote fails exact span matching (observed live:
    the model occasionally paraphrases). Never fuzzy-matches or accepts a bad quote;
    the second citation failure aborts like before.
    """
    extracted = generator.generate(Extraction, EXTRACTION, payload)
    unique_ids([e.evidence_id for e in extracted.evidence], "evidence")
    for attempt in range(2):
        try:
            return (
                extracted,
                [locate_evidence(e, spans, sources) for e in extracted.evidence],
                (attempt > 0),
            )
        except ResearchError as exc:
            if exc.code != "citation" or attempt:
                raise
            extracted = generator.generate(
                Extraction,
                EXTRACTION
                + "\nBản trước lỗi citation. Chỉ chọn span_id có thật, không xuất quote.",
                payload,
            )
            unique_ids([e.evidence_id for e in extracted.evidence], "evidence")
    raise AssertionError("unreachable")  # pragma: no cover


def validate_sources(sources: list[SourceDocument], settings: Settings) -> list[SourceDocument]:
    if len(sources) > settings.max_sources:
        raise ResearchError("source_limit", "Vượt số nguồn tối đa.")
    unique_ids([s.source_id for s in sources], "source")
    for source in sources:
        if text_hash(source.normalized_text) != source.content_hash:
            raise ResearchError("source_hash", "Snapshot đã thay đổi; cần đọc lại nguồn.")
        if len(source.normalized_text) > settings.max_source_chars:
            raise ResearchError("source_size", "Snapshot vượt giới hạn ký tự nguồn.")
    return group_sources(sources)


def build_payload(block: dict[str, JsonValue], settings: Settings, stage: str) -> str:
    payload = json.dumps(block, ensure_ascii=False)
    if len(payload) > settings.max_context_chars + 50000:
        raise ResearchError("prompt_limit", f"{stage} vượt ngân sách input; rút gọn nguồn.")
    return payload


def synthesize_and_validate(
    generator: Generator,
    synthesis_payload: str,
    *,
    request: ResearchRequest,
    evidence: list[Evidence],
    sources: list[SourceDocument],
    coverage: Coverage,
) -> tuple[Synthesis, ValidationResult, bool]:
    """Synthesize then strictly validate the draft.

    One bounded re-synthesis when the draft fails model-attributable checks
    (observed live: inference without reasoning, dangling evidence IDs).
    Validation stays strict; the second failure aborts like before.
    """
    draft = generator.generate(Synthesis, SYNTHESIS, synthesis_payload)
    for attempt in range(2):
        try:
            result = validate_synthesis(request, draft, evidence, sources, coverage)
        except ResearchError as exc:
            if exc.code not in ("dangling_id", "missing_support", "inference") or attempt:
                raise
            draft = generator.generate(
                Synthesis,
                SYNTHESIS
                + f"\nBản trước lỗi {exc.code}. Kiểm tra mọi ID và premise/assumptions/reasoning.",
                synthesis_payload,
            )
        else:
            return (*result, attempt > 0)
    raise AssertionError("unreachable")  # pragma: no cover


def run_research(
    request: ResearchRequest,
    sources: list[SourceDocument],
    generator: Generator,
    settings: Settings,
) -> ReportBundle:
    """Two generation stages. This module never loads fixtures, evaluation inputs or expected labels."""
    if not request.clarified:
        raise ResearchError(
            "needs_clarification",
            "Bạn muốn đánh giá theo nhu cầu, kiếm tiền, cạnh tranh hay tiêu chí khác?",
        )
    sources = validate_sources(sources, settings)
    spans, coverage = retrieve(request, sources, settings.max_context_chars)
    if not spans:
        raise ResearchError(
            "insufficient", "Không có văn bản đọc được; bổ sung nguồn/phạm vi cụ thể."
        )
    source_metadata: list[JsonValue] = [
        s.model_dump(mode="json", exclude={"normalized_text", "pages"}) for s in sources
    ]
    span_data: list[JsonValue] = [s.model_dump() for s in spans]
    payload = build_payload(
        {
            "request": request.model_dump(mode="json"),
            "sources": source_metadata,
            "untrusted_spans": span_data,
            "coverage": coverage.model_dump(),
        },
        settings,
        "Metadata và context",
    )
    extracted, evidence, citation_retried = extract_and_locate(generator, payload, spans, sources)
    coverage = coverage.model_copy(
        update={
            "warnings": [
                *coverage.warnings,
                "Bằng chứng được chọn lọc trong ngân sách đầu ra; span đã gửi không chứng minh đã trích đủ mọi phản chứng.",
            ]
        }
    )
    if citation_retried:
        coverage = coverage.model_copy(
            update={
                "warnings": [
                    *coverage.warnings,
                    "Một lượt trích xuất trước đó bị loại vì quote không khớp nguồn; đã sinh lại.",
                ]
            }
        )
    evidence_data: list[JsonValue] = [e.model_dump() for e in evidence]
    missing_data_json: list[JsonValue] = list(extracted.missing_data)
    synthesis_payload = build_payload(
        {
            "request": request.model_dump(mode="json"),
            "sources": source_metadata,
            "evidence": evidence_data,
            "extraction_missing_data": missing_data_json,
            "coverage": coverage.model_dump(),
        },
        settings,
        "Evidence và metadata",
    )
    draft_result, validation, synthesis_retried = synthesize_and_validate(
        generator,
        synthesis_payload,
        request=request,
        evidence=evidence,
        sources=sources,
        coverage=coverage,
    )
    result = draft_result
    if synthesis_retried:
        coverage = coverage.model_copy(
            update={
                "warnings": [
                    *coverage.warnings,
                    "Một bản tổng hợp trước đó bị loại vì thiếu premise/ID hỗ trợ; đã sinh lại.",
                ]
            }
        )
    assessments = [assess_source(request, source, sources) for source in sources]
    by_eid = {e.evidence_id: e for e in evidence}
    by_sid = {s.source_id: s for s in sources}
    for claim in result.claims:
        linked = {by_eid[link.evidence_id].source_id for link in claim.evidence_links}
        assessments.extend(
            assess_source(request, by_sid[sid], sources, claim) for sid in sorted(linked)
        )
    synthetic = any(s.is_synthetic for s in sources)
    report = ResearchReport(
        request=request,
        source_ids=[s.source_id for s in sources],
        assessments=assessments,
        evidence=evidence,
        claims=result.claims,
        conflicts=result.conflicts,
        recommendations=result.recommendations,
        missing_data=list(
            dict.fromkeys(extracted.missing_data + result.missing_data + coverage.warnings)
        ),
        coverage=coverage,
        is_synthetic=synthetic,
        mode="fixture" if synthetic else "live",
        model_id=generator.model_id,
        prompt_version=PROMPT_VERSION,
        source_hashes={s.source_id: s.content_hash for s in sources},
        usage=generator.usage(),
        validation=validation,
    )
    return ReportBundle(report=report, sources=sources)
