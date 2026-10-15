import ipaddress
import socket
import time
from http import HTTPStatus
from urllib.parse import urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup

from gamota_research.config import Settings
from gamota_research.contracts import SourceDocument
from gamota_research.errors import ResearchError
from gamota_research.ingestion.isolation import IngestJob, IngestLimits, isolated_ingest
from gamota_research.ingestion.normalize import document
from gamota_research.ingestion.pdf import parse_pdf_inner


def resolve_public(url: str, timeout: float) -> tuple[httpx.URL, str]:
    """Validate every DNS result; connect to the selected numeric IP with original TLS SNI."""
    del timeout  # The enclosing worker has a hard deadline including OS DNS resolution.
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ResearchError("unsafe_url", "Chỉ nhận URL http(s) công khai.")
        if parsed.username or parsed.password or parsed.port not in {None, 80, 443}:
            raise ResearchError("unsafe_url", "Không nhận credentials hoặc port ngoài 80/443.")
        host = parsed.hostname.encode("idna").decode("ascii")
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        ips = [str(address[4][0]) for address in addresses]
        parsed_ips = [ipaddress.ip_address(ip) for ip in ips]
        if not ips or any(
            not ip.is_global or ip.is_multicast or ip.is_reserved for ip in parsed_ips
        ):
            raise ResearchError(
                "unsafe_url", "Địa chỉ nội bộ/loopback/link-local/reserved bị chặn."
            )
        return httpx.URL(url), ips[0]
    except (ValueError, UnicodeError, socket.gaierror, httpx.InvalidURL) as exc:
        raise ResearchError("invalid_url", "URL hoặc DNS không hợp lệ.") from exc


def fetch_public(url: str, source_id: str, settings: Settings) -> SourceDocument:
    job = IngestJob(
        kind="url",
        source_id=source_id,
        name=source_id,
        payload=url,
        limits=IngestLimits.from_settings(settings),
    )
    return isolated_ingest(job, settings.http_timeout_seconds + 1).model_copy(
        update={"original_url": url},
    )


def read_response(response: httpx.Response, limits: IngestLimits, deadline: float) -> bytes:
    if response.headers.get("content-encoding", "identity").lower() != "identity":
        raise ResearchError("encoding", "Nguồn nén bị từ chối để giới hạn giải nén.")
    length = response.headers.get("content-length", "")
    if length.isdigit() and int(length) > limits.max_bytes:
        raise ResearchError("size_limit", "Nguồn vượt giới hạn tải xuống.")
    data = bytearray()
    for chunk in response.iter_raw():
        if time.monotonic() > deadline:
            raise ResearchError("timeout", "Tải nguồn quá thời gian.")
        if len(data) + len(chunk) > limits.max_bytes:
            raise ResearchError("size_limit", "Nguồn vượt giới hạn tải xuống.")
        data.extend(chunk)
    return bytes(data)


def parse_download(
    data: bytes, mime: str, source_id: str, url: str, limits: IngestLimits
) -> SourceDocument:
    if data.startswith(b"%PDF-"):
        return parse_pdf_inner(data, source_id, url, limits)
    if mime not in {"text/html", "application/xhtml+xml", "text/plain"} or b"\x00" in data:
        raise ResearchError("unsupported_type", "Chỉ đọc HTML/text và PDF có lớp chữ.")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ResearchError("encoding", "Chỉ hỗ trợ văn bản UTF-8; cần bản thay thế.") from exc
    title = source_id
    if mime != "text/plain":
        soup = BeautifulSoup(text, "html.parser")
        if soup.title:
            title = soup.title.get_text(" ", strip=True)[:300]
        for element in soup(
            ["head", "script", "style", "noscript", "nav", "footer", "header", "form"]
        ):
            element.decompose()
        text = soup.get_text("\n", strip=True)
    if not text.strip() or text.strip() == title.strip():
        raise ResearchError("empty_text", "Nguồn không có văn bản; có thể cần JS/OCR.")
    return document(source_id, title, text, limits.max_source_chars)


def fetch_inner(url: str, source_id: str, limits: IngestLimits) -> SourceDocument:
    deadline = time.monotonic() + limits.http_timeout_seconds
    current = url
    for _ in range(limits.max_redirects + 1):
        original, pinned_ip = resolve_public(current, limits.http_timeout_seconds)
        pinned = original.copy_with(host=pinned_ip)
        remaining = max(0.1, deadline - time.monotonic())
        transport = httpx.HTTPTransport(retries=0, trust_env=False)
        with (
            httpx.Client(
                transport=transport, timeout=remaining, trust_env=False, follow_redirects=False
            ) as client,
            client.stream(
                "GET",
                pinned,
                headers={
                    "Host": original.netloc.decode("ascii"),
                    "Accept-Encoding": "identity",
                    "User-Agent": "GamotaResearchMVP/0.1",
                },
                extensions={"sni_hostname": original.host},
            ) as response,
        ):
            if response.status_code in {301, 302, 303, 307, 308}:
                location = response.headers.get("location")
                if not location:
                    raise ResearchError("redirect", "Redirect không có đích.")
                next_url = urljoin(current, location)
                if original.scheme == "https" and urlsplit(next_url).scheme != "https":
                    raise ResearchError("redirect", "Chặn hạ cấp HTTPS.")
                current = next_url
                continue
            if response.status_code != HTTPStatus.OK:
                raise ResearchError("http_error", f"Nguồn trả HTTP {response.status_code}.")
            data = read_response(response, limits, deadline)
            mime = response.headers.get("content-type", "").split(";")[0].lower().strip()
            result = parse_download(data, mime, source_id, current, limits)
            return result.model_copy(update={"original_url": url})
    raise ResearchError("redirect_limit", "Vượt giới hạn redirect.")
