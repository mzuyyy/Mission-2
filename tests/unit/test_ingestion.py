from io import BytesIO

import pytest
from reportlab.pdfgen.canvas import Canvas

from gamota_research.config import Settings
from gamota_research.errors import ResearchError


def test_normalization_preserves_quote_offsets() -> None:
    # Given: decomposed Vietnamese and Windows line endings.
    from gamota_research.ingestion.normalize import document

    # When: normalizing a source once.
    source = document("S1", "Test", "Vie\u0323\u0302t\r\nmarket")
    # Then: the immutable text and hash describe the normalized snapshot.
    assert "\r" not in source.normalized_text
    assert len(source.content_hash) == 64


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "http://127.0.0.1/",
        "http://[::1]/",
        "http://169.254.169.254/",
        "http://10.0.0.1/",
        "http://user:pw@example.com/",
        "http://example.com:8080/",
    ],
)
def test_non_public_urls_are_rejected(url: str) -> None:
    # Given / When / Then: user supplied destinations cannot reach internal services.
    from gamota_research.ingestion.public_url import resolve_public

    with pytest.raises(ResearchError):
        resolve_public(url, 2)


def test_pdf_text_has_page_locator() -> None:
    from gamota_research.ingestion.pdf import parse_pdf

    # Given: a real text PDF, produced locally as synthetic input.
    output = BytesIO()
    canvas = Canvas(output)
    canvas.drawString(40, 700, "Quarter 3 downloads increased.")
    canvas.showPage()
    canvas.drawString(40, 700, "Revenue declined.")
    canvas.save()
    # When: parsing real PDF bytes.
    source = parse_pdf(output.getvalue(), "S1", "test.pdf", Settings())
    # Then: extracted evidence can be located on the original page.
    assert source.read_status == "ok"
    assert len(source.pages) == 2
    page = source.pages[1]
    assert "Revenue declined" in source.normalized_text[page.start_char : page.end_char]


def test_pdf_scan_reports_unsupported() -> None:
    from gamota_research.ingestion.pdf import parse_pdf

    # Given: PDF without a text layer.
    output = BytesIO()
    canvas = Canvas(output)
    canvas.rect(20, 20, 200, 200)
    canvas.showPage()
    canvas.save()
    # When / Then: no invented OCR result.
    source = parse_pdf(output.getvalue(), "S1", "scan.pdf", Settings())
    assert source.read_status == "unsupported"
    assert source.read_error


def test_executable_disguised_as_pdf_is_rejected() -> None:
    from gamota_research.ingestion.pdf import parse_pdf

    # Given / When: a misleading filename.
    source = parse_pdf(b"MZ binary", "S1", "report.pdf", Settings())
    # Then: file signature, not filename, controls acceptance.
    assert source.read_status == "unsupported"


def test_html_shell_does_not_count_title_as_read_content() -> None:
    from gamota_research.ingestion.isolation import IngestLimits
    from gamota_research.ingestion.public_url import parse_download

    # Given: a real-world failure shape: title metadata, empty body hydrated by JS.
    html = b'<html><head><title>Annual report</title></head><body><div id="root"></div><script>render()</script></body></html>'
    # When / Then: HTTP 200 and a title do not count as reading the report.
    with pytest.raises(ResearchError, match="empty_text"):
        parse_download(
            html, "text/html", "S1", "https://example.com", IngestLimits.from_settings(Settings())
        )
