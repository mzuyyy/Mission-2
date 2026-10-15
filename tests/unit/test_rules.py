from datetime import date

import pytest

from gamota_research.contracts import (
    Claim,
    ComparisonDimensions,
    Conflict,
    Evidence,
    EvidenceLink,
    Recommendation,
    ResearchRequest,
)
from gamota_research.errors import ResearchError
from gamota_research.ingestion.normalize import document
from gamota_research.models import Coverage, Synthesis


def request() -> ResearchRequest:
    return ResearchRequest(
        question="Có bằng chứng tăng trưởng không?",
        country=["VN"],
        platforms=["Android"],
        decision_goal="verify_claim",
        clarified=True,
        period_start=date(2025, 4, 1),
        period_end=date(2025, 9, 30),
    )


def sample_evidence(eid: str = "E1", gross: str = "gross") -> Evidence:
    source = document("S1", "Nguồn", "Revenue 20")
    return Evidence(
        evidence_id=eid,
        source_id="S1",
        content_hash=source.content_hash,
        quote="Revenue 20",
        start_char=0,
        end_char=10,
        surrounding_context="Revenue 20",
        subject="puzzle",
        metric="revenue",
        value=20,
        country="VN",
        platform="Android",
        period="2025-Q3",
        unit="million",
        currency="USD",
        gross_net=gross,
        actual_or_estimate="estimate",
    )


def test_gross_net_difference_is_not_same_scope_conflict() -> None:
    from gamota_research.validation import compare_evidence

    # Given: revenue has a different definition.
    a, b = sample_evidence(), sample_evidence("E2", "net")
    # When / Then: a contradiction is not asserted.
    assert compare_evidence([a, b])[0] is False


def test_unknown_dimensions_do_not_prove_comparability() -> None:
    from gamota_research.validation import compare_evidence

    # Given: currency is not known.
    a = sample_evidence().model_copy(update={"currency": None})
    # When / Then.
    assert compare_evidence([a, a])[0] == "unknown"


def test_same_scope_conflict_blocks_recommendation() -> None:
    from gamota_research.validation import validate_synthesis

    # Given: a synthesis attempts to recommend despite an unresolved comparable conflict.
    source = document("S1", "Test", "Revenue 20").model_copy(
        update={"country": ["VN"], "platforms": ["Android"], "data_period": "2025-Q2 to 2025-Q3"}
    )
    claim = Claim(
        claim_id="C1",
        text="Cần kiểm tra",
        kind="fact",
        assessment="supported",
        evidence_links=[EvidenceLink(evidence_id="E1", relation="supports")],
    )
    draft = Synthesis(
        claims=[claim],
        conflicts=[
            Conflict(
                conflict_id="X1",
                claim_ids=["C1"],
                evidence_ids=["E1", "E2"],
                comparison_dimensions=ComparisonDimensions(),
                same_scope=True,
                explanation="Nguồn khác số",
            )
        ],
        missing_data=[],
        recommendations=[
            Recommendation(
                recommendation_id="R1",
                action="Chọn ngay",
                rationale="Tăng trưởng",
                premise_claim_ids=["C1"],
                blocked=False,
                next_step="Khảo sát",
            )
        ],
    )
    # When: applying deterministic safeguards.
    result, _ = validate_synthesis(
        request(), draft, [sample_evidence(), sample_evidence("E2")], [source], Coverage()
    )
    # Then: report cannot present the affected recommendation as executable.
    assert result.recommendations[0].blocked
    assert result.claims[0].assessment == "conflicting"


def test_material_fact_without_support_is_rejected() -> None:
    from gamota_research.validation import validate_synthesis

    # Given: a model invents a material fact with no supporting evidence.
    draft = Synthesis(
        claims=[Claim(claim_id="C1", text="Profit is certain", kind="fact")],
        conflicts=[],
        recommendations=[],
        missing_data=[],
    )
    # When / Then: no usable report is produced.
    with pytest.raises(ResearchError, match="support"):
        validate_synthesis(request(), draft, [], [], Coverage())


def test_quote_existence_does_not_confirm_semantics() -> None:
    from gamota_research.validation import validate_synthesis

    # Given: a valid quote and source, but automatic checks cannot know its entailment.
    source = document("S1", "Nguồn", "Revenue 20")
    claim = Claim(
        claim_id="C1",
        text="Revenue 20",
        kind="fact",
        assessment="supported",
        evidence_links=[EvidenceLink(evidence_id="E1", relation="supports")],
    )
    draft = Synthesis(claims=[claim], conflicts=[], recommendations=[], missing_data=[])
    # When.
    result, checks = validate_synthesis(request(), draft, [sample_evidence()], [source], Coverage())
    # Then: unknown metadata limits the claim, and semantics still require human review.
    assert result.claims[0].assessment == "limited"
    assert checks.semantic_support == "human_review_required"
