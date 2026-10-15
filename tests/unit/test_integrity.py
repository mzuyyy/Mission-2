from datetime import date

import httpx
import pytest

from gamota_research.contracts import Claim, EvidenceLink
from gamota_research.errors import ResearchError
from gamota_research.ingestion.normalize import document
from gamota_research.llm import ChatGenerator
from gamota_research.models import Coverage, Synthesis
from gamota_research.pipeline import run_research
from gamota_research.retrieval import retrieve
from gamota_research.sources import assess_source, group_sources
from gamota_research.validation import validate_synthesis
from tests.integration.test_pipeline import WireFixture, configured
from tests.unit.test_rules import request, sample_evidence


def test_unknown_value_is_not_zero() -> None:
    # Given / When: qualitative evidence without a reported market metric.
    evidence = sample_evidence().model_copy(update={"value": None, "metric": None})
    # Then.
    assert evidence.value is None
    assert evidence.model_dump()["value"] is None


def test_source_post_date_cannot_replace_measurement_period() -> None:
    # Given: a recently posted source about old measurements.
    source = document("S1", "Old data", "Old data").model_copy(
        update={
            "published_at": date(2026, 1, 1),
            "data_period": "2023-Q2 to 2023-Q3",
            "country": ["VN"],
            "platforms": ["Android"],
        }
    )
    # When / Then.
    assessment = assess_source(request(), source, [source])
    assert assessment.freshness.value == "no"
    assert assessment.summary_label == "unsuitable"


def test_duplicate_snapshots_share_lineage_but_unknown_sources_do_not_become_independent() -> None:
    # Given: two copies and one unrelated document without known lineage.
    a = document("A", "A", "Same source")
    b = document("B", "B", "Same source")
    c = document("C", "C", "Another source")
    # When.
    grouped = group_sources([a, b, c])
    # Then.
    assert grouped[0].original_root_id == grouped[1].original_root_id
    assert assess_source(request(), grouped[2], grouped).independence.value == "unknown"


def test_retrieval_exposes_far_counterevidence_omission() -> None:
    # Given: long content larger than the chosen context budget.
    source = document("S1", "Long source", "game market " * 1000 + "\nCounterevidence at end.")
    # When.
    selected, coverage = retrieve(request(), [source], max_chars=1500)
    # Then: omission is visible and never described as exhaustive reading by the model.
    assert coverage.context_truncated
    assert coverage.omitted_span_ids
    assert coverage.selected_chars <= 1500
    assert selected


def test_evidence_country_mismatch_is_not_supported() -> None:
    # Given: source metadata matches the request but the individual metric is for another country.
    source = document("S1", "Test", "Revenue 20").model_copy(
        update={"country": ["VN"], "platforms": ["Android"], "data_period": "2025-Q2 to 2025-Q3"}
    )
    evidence = sample_evidence().model_copy(update={"country": "TH"})
    draft = Synthesis(
        claims=[
            Claim(
                claim_id="C1",
                text="VN revenue",
                kind="fact",
                assessment="supported",
                evidence_links=[EvidenceLink(evidence_id="E1", relation="supports")],
            )
        ],
        conflicts=[],
        recommendations=[],
        missing_data=[],
    )
    # When.
    result, _ = validate_synthesis(request(), draft, [evidence], [source], Coverage())
    # Then.
    assert result.claims[0].assessment == "insufficient"


def test_invalid_source_hash_is_rejected_before_sending_to_llm() -> None:
    # Given: a manipulated snapshot with a stale content hash.
    wire = WireFixture()
    source = document("S1", "Test", "Before").model_copy(update={"normalized_text": "After"})
    # When / Then.
    with pytest.raises(ResearchError, match="source_hash"):
        run_research(
            request(),
            [source],
            ChatGenerator(configured(), httpx.MockTransport(wire)),
            configured(),
        )
    assert wire.payloads == []
