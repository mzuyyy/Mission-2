from datetime import UTC, datetime, timedelta
from email.utils import format_datetime

import httpx
import pytest

from gamota_research.errors import ResearchError
from gamota_research.llm import ChatGenerator
from gamota_research.models import Extraction
from tests.integration.test_pipeline import configured, response


def test_upstream_shared_pool_error_is_actionable_without_echoing_raw_body() -> None:
    generator = ChatGenerator(
        configured(),
        httpx.MockTransport(
            lambda _req: httpx.Response(
                429,
                json={
                    "error": {
                        "message": "Provider returned error",
                        "metadata": {
                            "limit_source": "upstream_provider_shared_pool",
                            "raw": "private body test-only-not-a-real-key",
                        },
                    }
                },
            )
        ),
    )
    with pytest.raises(ResearchError, match="Pool") as caught:
        generator.generate(Extraction, "JSON", "{}")
    assert "private body" not in str(caught.value)
    assert "test-only-not-a-real-key" not in str(caught.value)
    assert generator.last_failure is not None
    assert generator.last_failure.category == "upstream_capacity"


def test_request_too_large_413_is_actionable_and_not_retried(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("gamota_research.llm.time.sleep", sleeps.append)
    generator = ChatGenerator(
        configured(),
        httpx.MockTransport(
            lambda _req: httpx.Response(
                413,
                json={
                    "error": {
                        "message": (
                            "Request too large for model openai/gpt-oss-20b on tokens per minute (TPM): "
                            "Limit 8000, Requested 10210, please reduce your message size"
                        )
                    }
                },
                headers={"Retry-After": "17"},
            )
        ),
    )
    with pytest.raises(ResearchError, match="giới hạn token") as caught:
        generator.generate(Extraction, "JSON", "{}")
    assert "reduce your message size" not in str(caught.value)
    assert sleeps == []
    assert generator.usage().request_count == 1
    assert generator.last_failure is not None
    assert generator.last_failure.category == "payload_too_large"


def test_daily_limit_does_not_waste_a_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("gamota_research.llm.time.sleep", sleeps.append)
    generator = ChatGenerator(
        configured(),
        httpx.MockTransport(
            lambda _req: httpx.Response(
                429, json={"error": {"message": "Rate limit exceeded: free-models-per-day"}}
            )
        ),
    )
    with pytest.raises(ResearchError, match="hạn mức ngày"):
        generator.generate(Extraction, "JSON", "{}")
    assert generator.usage().request_count == 1
    assert sleeps == []


@pytest.mark.parametrize("http_date", [False, True])
def test_retry_waits_for_provider_delay(
    monkeypatch: pytest.MonkeyPatch, *, http_date: bool
) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("gamota_research.llm.time.sleep", sleeps.append)
    retry_after = format_datetime(datetime.now(UTC) + timedelta(seconds=9)) if http_date else "8"
    replies = iter(
        [httpx.Response(429, headers={"Retry-After": retry_after}), response('{"evidence":[]}')]
    )
    generator = ChatGenerator(configured(), httpx.MockTransport(lambda _req: next(replies)))
    assert generator.generate(Extraction, "JSON", "{}").evidence == []
    assert len(sleeps) == 1
    assert 7 <= sleeps[0] <= 10
    assert generator.usage().request_count == 2


def test_long_retry_after_returns_hint_without_sleep_or_early_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("gamota_research.llm.time.sleep", sleeps.append)
    generator = ChatGenerator(
        configured(),
        httpx.MockTransport(lambda _req: httpx.Response(429, headers={"Retry-After": "120"})),
    )
    with pytest.raises(ResearchError, match="120"):
        generator.generate(Extraction, "JSON", "{}")
    assert sleeps == []
    assert generator.usage().request_count == 1
