from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError, PyPdfError

from gamota_research.config import Settings
from gamota_research.contracts import PageRange, SourceDocument
from gamota_research.ingestion.isolation import (
    IngestJob,
    IngestLimits,
    encode_pdf,
    isolated_ingest,
)
from gamota_research.ingestion.normalize import document, failed_document, normalize


def parse_pdf(data: bytes, source_id: str, name: str, settings: Settings) -> SourceDocument:
    if len(data) > settings.max_bytes:
        return failed_document(source_id, name, "Tệp vượt giới hạn dung lượng.")
    if not data.startswith(b"%PDF-"):
        return failed_document(source_id, name, "Nội dung thực không phải PDF.").model_copy(
            update={"read_status": "unsupported"},
        )
    job = IngestJob(
        kind="pdf",
        source_id=source_id,
        name=name,
        payload=encode_pdf(data),
        limits=IngestLimits.from_settings(settings),
    )
    return isolated_ingest(job, settings.pdf_timeout_seconds).model_copy(
        update={"local_name": name}
    )


def parse_pdf_inner(data: bytes, source_id: str, name: str, limits: IngestLimits) -> SourceDocument:
    """Only called inside a disposable worker; PDF is never executed."""
    try:
        reader = PdfReader(BytesIO(data), strict=False)
        if reader.is_encrypted:
            return failed_document(source_id, name, "PDF mã hóa; cần bản có quyền đọc.")
        texts: list[str] = []
        pages: list[PageRange] = []
        position = 0
        partial = len(reader.pages) > limits.max_pdf_pages
        empty_pages: list[int] = []
        for index, page in enumerate(reader.pages[: limits.max_pdf_pages], 1):
            text = normalize(page.extract_text() or "")
            if not text.strip():
                empty_pages.append(index)
            remaining = limits.max_source_chars - position
            if len(text) > remaining:
                text = text[:remaining]
                partial = True
            texts.append(text)
            pages.append(
                PageRange(page_number=index, start_char=position, end_char=position + len(text))
            )
            position += len(text) + 2
            if position >= limits.max_source_chars:
                partial = True
                break
        result = document(source_id, name, "\n\n".join(texts), limits.max_source_chars)
        if not result.normalized_text.strip():
            return result.model_copy(
                update={
                    "read_status": "unsupported",
                    "pages": pages,
                    "read_error": "PDF không có lớp chữ đọc được; OCR chưa hỗ trợ.",
                }
            )
        issues: list[str] = []
        if partial:
            issues.append("PDF bị cắt theo giới hạn trang/ký tự.")
        if empty_pages:
            issues.append(f"Trang không có chữ trích xuất được: {empty_pages}. Không có OCR.")
        return result.model_copy(
            update={
                "pages": pages,
                "read_status": "partial" if issues else "ok",
                "read_error": " ".join(issues) or None,
            }
        )
    except (PyPdfError, PdfReadError, ValueError, KeyError, TypeError, OSError):
        return failed_document(source_id, name, "PDF hỏng hoặc cấu trúc chưa hỗ trợ.")
