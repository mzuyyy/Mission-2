from datetime import UTC, datetime, timedelta
from email.utils import format_datetime

import httpx
import pytest
from pydantic import SecretStr

from gamota_research.config import Settings
from gamota_research.errors import ResearchError
from gamota_research.llm import ChatGenerator
from gamota_research.models import Extraction
from tests.integration.test_pipeline import configured, response


def configured_with_fallback() -> Settings:
    return Settings(
        _env_file=None,
        llm_api_base="https://primary.example/v1",
        llm_api_key=SecretStr("test-only-not-a-real-key"),
        llm_model="primary-model",
        fallback_llm_api_base="https://fallback.example/v1",
        fallback_llm_api_key=SecretStr("test-only-not-a-real-key"),
        fallback_llm_model="fallback-model",
    )


def test_retryable_switches_to_fallback_once_without_sleep(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("gamota_research.llm.time.sleep", sleeps.append)
    calls: list[str] = []

    def handler(req: httpx.Request) -> httpx.Response:
        calls.append(str(req.url))
        if "primary.example" in str(req.url):
            return httpx.Response(429, headers={"Retry-After": "5"})
        body = response('{"evidence":[]}')
        assert '"fallback-model"' in req.content.decode("utf-8")
        return body

    generator = ChatGenerator(configured_with_fallback(), httpx.MockTransport(handler))
    assert generator.generate(Extraction, "JSON", "{}").evidence == []
    assert len(calls) == 2
    assert "primary.example" in calls[0]
    assert "fallback.example" in calls[1]
    assert sleeps == []
    assert generator.using_fallback
    assert generator.model_id == "fallback-model"
    assert generator.usage().request_count == 2


def test_fallback_failure_aborts_without_third_provider() -> None:
    replies = iter(
        [
            httpx.Response(429, headers={"Retry-After": "1"}),
            httpx.Response(429, headers={"Retry-After": "1"}),
        ]
    )
    generator = ChatGenerator(
        configured_with_fallback(), httpx.MockTransport(lambda _req: next(replies))
    )
    with pytest.raises(ResearchError, match="provider_retryable"):
        generator.generate(Extraction, "JSON", "{}")
    assert generator.usage().request_count == 2
    assert generator.using_fallback


def test_no_fallback_configured_keeps_old_wait_behavior() -> None:
    generator = ChatGenerator(configured(), httpx.MockTransport(lambda _req: httpx.Response(200)))
    assert not generator.using_fallback
    assert generator.model_id == "mock-wire"


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
