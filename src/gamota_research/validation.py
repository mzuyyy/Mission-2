from gamota_research.contracts import (
    Claim,
    Conflict,
    Evidence,
    Recommendation,
    ResearchRequest,
    SourceDocument,
)
from gamota_research.errors import ResearchError
from gamota_research.models import Coverage, Synthesis, ValidationResult
from gamota_research.sources import assess_source
from gamota_research.validation_helpers import check_graph, compare_evidence, unique_ids

__all__ = ["compare_evidence", "unique_ids", "validate_synthesis"]


def _validate_claims(
    request: ResearchRequest,
    draft: Synthesis,
    evidence: list[Evidence],
    sources: list[SourceDocument],
    coverage: Coverage,
) -> list[Claim]:
    by_eid = {e.evidence_id: e for e in evidence}
    by_sid = {s.source_id: s for s in sources}
    claims: list[Claim] = []
    for claim in draft.claims:
        if any(link.evidence_id not in by_eid for link in claim.evidence_links):
            raise ResearchError("dangling_id", f"{claim.claim_id}: evidence ID không tồn tại.")
        supports = [
            by_eid[link.evidence_id] for link in claim.evidence_links if link.relation == "supports"
        ]
        if claim.kind == "fact" and claim.material and not supports:
            raise ResearchError(
                "missing_support", f"{claim.claim_id}: material fact thiếu support."
            )
        if claim.kind == "inference" and (
            not claim.premise_claim_ids or not claim.assumptions or not claim.reasoning
        ):
            raise ResearchError("inference", f"{claim.claim_id}: thiếu premise/giả định/lập luận.")
        label = claim.assessment
        limitations = list(claim.limitations)
        assessments = [
            assess_source(request, by_sid[e.source_id], sources, claim) for e in supports
        ]
        evidence_assessments = [
            assess_source(
                request,
                by_sid[e.source_id].model_copy(
                    update={
                        "country": [e.country] if e.country else by_sid[e.source_id].country,
                        "platforms": [e.platform] if e.platform else by_sid[e.source_id].platforms,
                        "data_period": e.period or by_sid[e.source_id].data_period,
                        "period_start": None if e.period else by_sid[e.source_id].period_start,
                        "period_end": None if e.period else by_sid[e.source_id].period_end,
                    }
                ),
                sources,
                claim,
            )
            for e in supports
        ]
        if any(a.summary_label == "unsuitable" for a in assessments + evidence_assessments):
            label = "insufficient"
            limitations.append("Có support nằm ngoài phạm vi/kỳ đo hoặc nguồn không đọc được.")
        elif label == "supported" and (
            not assessments or any(a.summary_label != "strong_for_this_claim" for a in assessments)
        ):
            label = "limited"
            limitations.append(
                "Metadata/phương pháp/độc lập chưa đủ; cần đọc và đánh giá ngữ nghĩa."
            )
        if coverage.context_truncated or coverage.partial_sources or coverage.failed_sources:
            if label == "supported":
                label = "limited"
            limitations.append("Coverage chưa đủ; có thể thiếu phản chứng.")
        if claim.kind == "hypothesis":
            label = "insufficient"
        claims.append(
            claim.model_copy(
                update={
                    "assessment": label,
                    "limitations": list(dict.fromkeys(limitations)),
                    "human_review": "unreviewed",
                }
            )
        )
    return claims


def _validate_conflicts(
    draft: Synthesis, evidence: list[Evidence], claims: list[Claim]
) -> tuple[list[Conflict], set[str]]:
    by_eid = {e.evidence_id: e for e in evidence}
    by_cid = {c.claim_id: c for c in claims}
    by_rid = {r.recommendation_id: r for r in draft.recommendations}
    conflicts: list[Conflict] = []
    affected: set[str] = set()
    for original in draft.conflicts:
        conflict = original
        if (
            any(eid not in by_eid for eid in conflict.evidence_ids)
            or any(cid not in by_cid for cid in conflict.claim_ids)
            or any(rid not in by_rid for rid in conflict.affected_recommendation_ids)
        ):
            raise ResearchError("dangling_id", f"{conflict.conflict_id}: ID không tồn tại.")
        same, dims = compare_evidence([by_eid[eid] for eid in conflict.evidence_ids])
        explanation = conflict.explanation
        if same is not True:
            explanation += " Code: khác phạm vi hoặc chưa đủ dimensions; chưa xác nhận mâu thuẫn."
        conflict = conflict.model_copy(
            update={
                "same_scope": same,
                "comparison_dimensions": dims,
                "unresolved": same is not False,
                "explanation": explanation,
            }
        )
        if conflict.unresolved:
            affected.update(conflict.claim_ids)
            affected.update(
                c.claim_id
                for c in claims
                if any(link.evidence_id in conflict.evidence_ids for link in c.evidence_links)
            )
        conflicts.append(conflict)
    return conflicts, affected


def _propagate_claims(
    claims: list[Claim], conflicts: list[Conflict], affected: set[str]
) -> list[Claim]:
    # Uncertainty propagates through the premise graph, including multi-level inferences.
    resolved = claims
    for _ in resolved:
        current = {c.claim_id: c for c in resolved}
        updated: list[Claim] = []
        for original in resolved:
            claim = original
            if claim.claim_id in affected:
                comparable = any(
                    c.same_scope is True and claim.claim_id in c.claim_ids for c in conflicts
                )
                claim = claim.model_copy(
                    update={"assessment": "conflicting" if comparable else "insufficient"}
                )
            if claim.premise_claim_ids and any(
                current[cid].assessment in {"insufficient", "conflicting"}
                for cid in claim.premise_claim_ids
            ):
                claim = claim.model_copy(update={"assessment": "insufficient"})
            updated.append(claim)
        resolved = updated
    return resolved


def _validate_recommendations(
    draft: Synthesis, claims: list[Claim], conflicts: list[Conflict], coverage: Coverage
) -> list[Recommendation]:
    by_cid = {c.claim_id: c for c in claims}
    current = {c.claim_id: c for c in claims}
    recommendations: list[Recommendation] = []
    for recommendation in draft.recommendations:
        if any(cid not in by_cid for cid in recommendation.premise_claim_ids):
            raise ResearchError("dangling_id", "Recommendation có premise ID không tồn tại.")
        blockers = list(recommendation.blocking_unknowns)
        if not recommendation.premise_claim_ids:
            blockers.append("Chưa có premise cho lựa chọn; chỉ thực hiện bước bổ sung dữ liệu.")
        if any(current[cid].assessment != "supported" for cid in recommendation.premise_claim_ids):
            blockers.append("Premise còn limited/conflicting/insufficient; cần người kiểm chứng.")
        if any(
            c.unresolved
            and (
                recommendation.recommendation_id in c.affected_recommendation_ids
                or bool(set(c.claim_ids) & set(recommendation.premise_claim_ids))
            )
            for c in conflicts
        ):
            blockers.append("Mâu thuẫn/chưa rõ so sánh chưa giải quyết.")
        if coverage.context_truncated or coverage.failed_sources or coverage.partial_sources:
            blockers.append("Coverage chưa đầy đủ.")
        recommendations.append(
            recommendation.model_copy(
                update={
                    "blocking_unknowns": list(dict.fromkeys(blockers)),
                    "blocked": recommendation.blocked or bool(blockers),
                }
            )
        )
    return recommendations


def validate_synthesis(
    request: ResearchRequest,
    draft: Synthesis,
    evidence: list[Evidence],
    sources: list[SourceDocument],
    coverage: Coverage,
) -> tuple[Synthesis, ValidationResult]:
    unique_ids([c.claim_id for c in draft.claims], "claim")
    unique_ids([c.conflict_id for c in draft.conflicts], "conflict")
    unique_ids([r.recommendation_id for r in draft.recommendations], "recommendation")
    check_graph(draft.claims)
    claims = _validate_claims(request, draft, evidence, sources, coverage)
    conflicts, affected = _validate_conflicts(draft, evidence, claims)
    claims = _propagate_claims(claims, conflicts, affected)
    recommendations = _validate_recommendations(draft, claims, conflicts, coverage)
    checks = ["Context bị cắt: chưa đánh giá completeness."] if coverage.context_truncated else []
    result = draft.model_copy(
        update={"claims": claims, "conflicts": conflicts, "recommendations": recommendations}
    )
    return result, ValidationResult(quote_checks=len(evidence), failures=checks)
