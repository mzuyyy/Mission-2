import httpx
import pytest

from gamota_research.citations import check_evidence, locate_evidence
from gamota_research.errors import ResearchError
from gamota_research.ingestion.normalize import document
from gamota_research.llm import ChatGenerator
from gamota_research.models import EvidenceDraft, Extraction, Span
from tests.integration.test_pipeline import configured, response


def test_span_selection_uses_exact_snapshot_without_model_retyping() -> None:
    source = document("S1", "PDF text", "Heading\nRevenue\n  20 million.\nOther text.")
    text = source.normalized_text[8:28]
    span = Span(span_id="S1_span", source_id="S1", start_char=8, end_char=28, text=text)
    draft = EvidenceDraft(evidence_id="E1", source_id="S1", span_id="S1_span")
    evidence = locate_evidence(draft, [span], [source])
    assert evidence.quote == text
    assert evidence.start_char == 8
    assert evidence.end_char == 28
    assert evidence.value is None
    check_evidence(evidence, source)


def test_span_selection_rejects_unknown_source_or_span() -> None:
    source = document("S1", "PDF text", "Revenue unknown")
    draft = EvidenceDraft(evidence_id="E1", source_id="S1", span_id="invented")
    with pytest.raises(ResearchError, match="span/source"):
        locate_evidence(draft, [], [source])


def test_truncated_output_retry_changes_instructions_without_raising_cap() -> None:
    received: list[httpx.Request] = []

    def handler(req: httpx.Request) -> httpx.Response:
        received.append(req)
        if len(received) == 1:
            return httpx.Response(
                200, json={"choices": [{"message": {"content": "{"}, "finish_reason": "length"}]}
            )
        return response('{"evidence":[]}')

    generator = ChatGenerator(configured(), httpx.MockTransport(handler))
    assert generator.generate(Extraction, "JSON", "{}").evidence == []
    assert received[0].content != received[1].content
    assert generator.settings.max_output_tokens == 2500
    assert generator.usage().request_count == 2
