from pathlib import Path

from gamota_research.citations import check_evidence
from gamota_research.contracts import Claim, ReviewDecision, new_id
from gamota_research.errors import ResearchError
from gamota_research.ingestion.normalize import text_hash
from gamota_research.models import ReportBundle, ReviewEvent, Synthesis
from gamota_research.validation import unique_ids, validate_synthesis


class Workspace:
    """Per-session random directory; exclusive writes preserve every previous version."""

    def __init__(self, root: Path = Path("runs")) -> None:
        self.path = root / new_id()
        self.path.mkdir(parents=True, exist_ok=False)

    def save(self, bundle: ReportBundle) -> Path:
        validated = ReportBundle.model_validate_json(bundle.model_dump_json())
        name = f"{validated.report.report_id}_v{validated.report.version}.json"
        destination = self.path / name
        with destination.open("x", encoding="utf-8") as output:
            output.write(validated.model_dump_json(indent=2))
        return destination


def review(
    bundle: ReportBundle,
    claim_id: str,
    decision: ReviewDecision,
    note: str,
    edited_text: str | None = None,
) -> ReportBundle:
    report = bundle.report
    if claim_id not in {c.claim_id for c in report.claims}:
        raise ResearchError("review_id", "Không tìm thấy nhận định cần đánh giá.")
    if decision == "unreviewed":
        raise ResearchError("review_decision", "Chọn accept/needs_review/reject.")
    if edited_text is not None and not edited_text.strip():
        raise ResearchError("review_text", "Nội dung chỉnh sửa không được trống.")
    claims: list[Claim] = []
    for original in report.claims:
        claim = original
        if claim.claim_id == claim_id:
            edits: dict[str, str | list[str]] = {"human_review": decision}
            if edited_text is not None and edited_text != claim.text:
                edits.update(
                    text=edited_text,
                    assessment="insufficient",
                    limitations=[
                        *claim.limitations,
                        "Nội dung được người dùng sửa; cần đánh giá lại hỗ trợ ngữ nghĩa.",
                    ],
                )
            claim = Claim.model_validate({**claim.model_dump(), **edits})
        claims.append(claim)
    event = ReviewEvent(
        report_id=report.report_id,
        claim_id=claim_id,
        previous_version=report.version,
        new_version=report.version + 1,
        decision=decision,
        note=note,
        previous_claim=next(c for c in report.claims if c.claim_id == claim_id),
        new_claim=next(c for c in claims if c.claim_id == claim_id),
    )
    # Rejection/edits propagate through dependent claims before recommendations are reconsidered.
    affected = {
        c.claim_id
        for c in claims
        if c.human_review in {"reject", "needs_review"}
        or c.assessment in {"conflicting", "insufficient"}
    }
    for _ in claims:
        affected.update(c.claim_id for c in claims if set(c.premise_claim_ids) & affected)
    recommendations = [
        r.model_copy(
            update={
                "blocked": True,
                "blocking_unknowns": list(
                    dict.fromkeys([*r.blocking_unknowns, "Premise cần kiểm tra sau review."])
                ),
            }
        )
        if set(r.premise_claim_ids) & affected
        else r
        for r in report.recommendations
    ]
    updated = report.model_copy(
        update={
            "claims": claims,
            "recommendations": recommendations,
            "version": event.new_version,
            "review_history": [*report.review_history, event],
        }
    )
    return bundle.model_copy(update={"report": updated})


def load_bundle(data: bytes, max_bytes: int = 30_000_000) -> ReportBundle:
    if len(data) > max_bytes:
        raise ResearchError("replay_size", "JSON vượt giới hạn dung lượng.")
    bundle = ReportBundle.model_validate_json(data)
    report = bundle.report
    unique_ids([s.source_id for s in bundle.sources], "source")
    unique_ids([e.evidence_id for e in report.evidence], "evidence")
    by_sid = {s.source_id: s for s in bundle.sources}
    actual_hashes = {s.source_id: text_hash(s.normalized_text) for s in bundle.sources}
    if report.source_hashes != actual_hashes or set(report.source_ids) != set(by_sid):
        raise ResearchError("replay_hash", "Snapshot không khớp danh sách nguồn/hash report.")
    for source in bundle.sources:
        if source.content_hash != actual_hashes[source.source_id]:
            raise ResearchError("replay_hash", "Hash snapshot nguồn không hợp lệ.")
    for evidence in report.evidence:
        source = by_sid.get(evidence.source_id)
        if not source:
            raise ResearchError("replay_id", "Evidence trỏ tới nguồn không tồn tại.")
        check_evidence(evidence, source)
    draft = Synthesis(
        claims=report.claims,
        conflicts=report.conflicts,
        recommendations=report.recommendations,
        missing_data=report.missing_data,
    )
    validated, checks = validate_synthesis(
        report.request, draft, report.evidence, bundle.sources, report.coverage
    )
    claims = [
        claim.model_copy(update={"human_review": original.human_review})
        for claim, original in zip(validated.claims, report.claims, strict=True)
    ]
    synthetic = report.is_synthetic or any(s.is_synthetic for s in bundle.sources)
    replay = report.model_copy(
        update={
            "mode": "replay",
            "is_synthetic": synthetic,
            "claims": claims,
            "conflicts": validated.conflicts,
            "recommendations": validated.recommendations,
            "validation": checks,
        }
    )
    return bundle.model_copy(update={"report": replay})
