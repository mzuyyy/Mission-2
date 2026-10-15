import base64
import subprocess
import sys
from typing import Literal

from pydantic import Field, ValidationError

from gamota_research.config import Settings
from gamota_research.contracts import Contract, SourceDocument
from gamota_research.ingestion.normalize import failed_document


class IngestLimits(Contract):
    max_bytes: int = Field(gt=0)
    max_pdf_pages: int = Field(gt=0)
    max_source_chars: int = Field(gt=0)
    http_timeout_seconds: float = Field(gt=0)
    max_redirects: int = Field(ge=0)

    @classmethod
    def from_settings(cls, settings: Settings) -> "IngestLimits":
        return cls(
            max_bytes=settings.max_bytes,
            max_pdf_pages=settings.max_pdf_pages,
            max_source_chars=settings.max_source_chars,
            http_timeout_seconds=settings.http_timeout_seconds,
            max_redirects=settings.max_redirects,
        )


class IngestJob(Contract):
    kind: Literal["url", "pdf"]
    source_id: str
    name: str
    payload: str
    limits: IngestLimits


def isolated_ingest(job: IngestJob, timeout: float) -> SourceDocument:
    """Kill the parser/download child on wall-clock expiry, including blocked DNS."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "gamota_research.ingestion.worker"],
            input=job.model_dump_json().encode("utf-8"),
            capture_output=True,
            timeout=timeout,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        if result.returncode or len(result.stdout) > job.limits.max_source_chars * 8 + 100000:
            return failed_document(job.source_id, job.name, "Worker đọc nguồn thất bại.")
        return SourceDocument.model_validate_json(result.stdout)
    except subprocess.TimeoutExpired:
        return failed_document(job.source_id, job.name, "Đọc nguồn quá thời gian cho phép.")
    except (OSError, ValidationError):
        return failed_document(job.source_id, job.name, "Không thể chạy/đọc kết quả parser.")


def encode_pdf(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")
