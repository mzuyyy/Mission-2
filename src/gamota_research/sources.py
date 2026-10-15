from gamota_research.contracts import (
    Claim,
    Dimension,
    ResearchRequest,
    SourceAssessment,
    SourceDocument,
)
from gamota_research.scope import freshness_dimension, scope_dimension


def group_sources(sources: list[SourceDocument]) -> list[SourceDocument]:
    """Exact duplicates share one root; distinct URLs/domains never prove independence."""
    by_hash: dict[str, list[SourceDocument]] = {}
    for source in sources:
        if source.normalized_text:
            by_hash.setdefault(source.content_hash, []).append(source)
    result: list[SourceDocument] = []
    for original in sources:
        source = original
        duplicates = by_hash.get(source.content_hash, [])
        if len(duplicates) > 1:
            roots = {s.original_root_id for s in duplicates if s.original_root_id}
            root = next(iter(roots)) if len(roots) == 1 else f"copy_{source.content_hash[:20]}"
            source = source.model_copy(
                update={
                    "original_root_id": root,
                    "root_relation_reason": "Snapshot trùng hoàn toàn SHA-256; không đếm độc lập.",
                    "metadata_provenance": {
                        **source.metadata_provenance,
                        "original_root_id": "heuristic",
                    },
                }
            )
        result.append(source)
    return result


def assess_source(
    request: ResearchRequest,
    source: SourceDocument,
    all_sources: list[SourceDocument],
    claim: Claim | None = None,
) -> SourceAssessment:
    origin = Dimension(
        value="partial" if source.publisher else "unknown",
        rationale=f"Publisher: {source.publisher or 'unknown'}; loại: {source.source_kind}. "
        "Xuất xứ chưa chứng minh hỗ trợ ngữ nghĩa.",
        provenance=source.metadata_provenance.get("publisher", "heuristic"),
    )
    methodology = Dimension(
        value="partial" if source.methodology else "unknown",
        rationale=source.methodology or "Chưa biết phương pháp, mẫu và sai số.",
        provenance=source.metadata_provenance.get("methodology", "heuristic"),
    )
    interest = Dimension(
        value="partial" if source.conflicts_of_interest else "unknown",
        rationale=source.conflicts_of_interest or "Chưa xác định lợi ích của bên công bố.",
        provenance=source.metadata_provenance.get("conflicts_of_interest", "heuristic"),
    )
    shared = bool(
        source.original_root_id
        and any(
            s.source_id != source.source_id and s.original_root_id == source.original_root_id
            for s in all_sources
        )
    )
    independence = Dimension(
        value="no" if shared else "unknown",
        rationale=source.root_relation_reason
        + (" Có nguồn cùng gốc trong lượt này." if shared else " Chưa xác nhận độc lập."),
        provenance=source.metadata_provenance.get("original_root_id", "heuristic"),
    )
    scope = scope_dimension(request, source)
    freshness = freshness_dimension(request, source)
    unsuitable = scope.value == "no" or freshness.value == "no" or not source.normalized_text
    strong = bool(
        source.methodology
        and source.conflicts_of_interest
        and source.publisher
        and source.original_root_id
        and scope.value == "yes"
        and freshness.value == "yes"
        and source.read_status == "ok"
        and source.source_kind in {"original_report", "company_disclosure"}
    )
    return SourceAssessment(
        source_id=source.source_id,
        claim_or_question_id=claim.claim_id if claim else request.request_id,
        origin=origin,
        methodology=methodology,
        scope=scope,
        freshness=freshness,
        interest=interest,
        independence=independence,
        summary_label="unsuitable"
        if unsuitable
        else ("strong_for_this_claim" if strong else "limited"),
    )
