import socket

import httpx
import pytest

from gamota_research.config import Settings
from gamota_research.errors import ResearchError
from gamota_research.ingestion.isolation import IngestLimits
from gamota_research.ingestion.public_url import fetch_inner, resolve_public


def test_mixed_public_private_dns_answers_are_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    # Given: a public hostname also resolves to a metadata address.
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", 443)),
        ],
    )
    # When / Then.
    with pytest.raises(ResearchError, match="unsafe_url"):
        resolve_public("https://example.com/report", 2)


def test_connection_pins_ip_and_retains_host_sni(monkeypatch: pytest.MonkeyPatch) -> None:
    # Given: DNS is checked once then the transport sees only the approved numeric IP.
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ],
    )
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            headers={"content-type": "text/plain"},
            stream=httpx.ByteStream(b"Actual source content"),
        )

    monkeypatch.setattr(httpx, "HTTPTransport", lambda **_kwargs: httpx.MockTransport(handler))
    # When.
    source = fetch_inner("https://example.com/report", "S1", IngestLimits.from_settings(Settings()))
    # Then: no second hostname lookup can rebind the TCP target.
    assert source.normalized_text == "Actual source content"
    assert seen[0].url.host == "93.184.216.34"
    assert seen[0].headers["host"] == "example.com"
    assert seen[0].extensions["sni_hostname"] == "example.com"


def test_redirect_to_private_ip_is_blocked_before_second_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def resolve(
        host: str, *args: str, **kwargs: str
    ) -> list[tuple[int, int, int, str, tuple[str, int]]]:
        ip = "127.0.0.1" if host == "127.0.0.1" else "93.184.216.34"
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 443))]

    # Given: an otherwise public page redirects to localhost.
    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(302, headers={"location": "https://127.0.0.1/private"})

    monkeypatch.setattr(httpx, "HTTPTransport", lambda **_kwargs: httpx.MockTransport(handler))
    # When / Then.
    with pytest.raises(ResearchError, match="unsafe_url"):
        fetch_inner("https://example.com", "S1", IngestLimits.from_settings(Settings()))
    assert len(seen) == 1


def test_stream_without_content_length_cannot_exceed_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from gamota_research.ingestion.public_url import read_response

    # Given: streaming bytes without a Content-Length header.
    response = httpx.Response(200, stream=httpx.ByteStream(b"0123456789"))
    limits = IngestLimits.from_settings(Settings()).model_copy(update={"max_bytes": 5})
    # When / Then.
    with pytest.raises(ResearchError, match="size_limit"):
        read_response(response, limits, float("inf"))
