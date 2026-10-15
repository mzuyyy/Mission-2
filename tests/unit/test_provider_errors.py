import json

import httpx
import pytest

from gamota_research.errors import ResearchError
from gamota_research.llm import ChatGenerator
from gamota_research.models import Extraction
from tests.integration.test_pipeline import configured, response


def test_auth_failure_has_no_retry_or_secret_in_error() -> None:
    # Given: unsafe provider body, only status may reach the user.
    generator = ChatGenerator(
        configured(),
        httpx.MockTransport(
            lambda _req: httpx.Response(401, text="test-only-not-a-real-key private body")
        ),
    )
    # When / Then.
    with pytest.raises(ResearchError, match="provider_http") as caught:
        generator.generate(Extraction, "JSON", "{}")
    assert "private body" not in str(caught.value)
    assert "test-only-not-a-real-key" not in str(caught.value)
    assert generator.usage().request_count == 1
    assert generator.usage().tokens is None


def test_rate_limit_retry_uses_same_endpoint_and_budget() -> None:
    # Given: transient rate limiting followed by a valid response.
    received: list[httpx.Request] = []

    def handler(req: httpx.Request) -> httpx.Response:
        received.append(req)
        if len(received) == 1:
            return httpx.Response(429)
        return response('{"evidence": []}')

    generator = ChatGenerator(configured(), httpx.MockTransport(handler))
    # When.
    result = generator.generate(Extraction, "JSON", "{}")
    # Then.
    assert result.evidence == []
    assert generator.usage().request_count == 2
    assert received[0].url == received[1].url
    assert json.loads(received[0].content)["model"] == json.loads(received[1].content)["model"]


def test_model_output_truncation_produces_no_report() -> None:
    # Given: provider indicates truncation, even with parseable JSON.
    generator = ChatGenerator(
        configured(),
        httpx.MockTransport(
            lambda _req: httpx.Response(
                200,
                json={
                    "choices": [
                        {"message": {"content": '{"evidence": []}'}, "finish_reason": "length"}
                    ]
                },
            )
        ),
    )
    # When / Then.
    with pytest.raises(ResearchError, match="provider_incomplete"):
        generator.generate(Extraction, "JSON", "{}")
