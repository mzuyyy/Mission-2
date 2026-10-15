import base64
import sys

import httpx

from gamota_research.errors import ResearchError
from gamota_research.ingestion.isolation import IngestJob
from gamota_research.ingestion.normalize import failed_document
from gamota_research.ingestion.pdf import parse_pdf_inner
from gamota_research.ingestion.public_url import fetch_inner


def main() -> None:
    job = IngestJob.model_validate_json(sys.stdin.buffer.read())
    try:
        match job.kind:
            case "pdf":
                result = parse_pdf_inner(
                    base64.b64decode(job.payload), job.source_id, job.name, job.limits
                )
            case "url":
                result = fetch_inner(job.payload, job.source_id, job.limits)
    except ResearchError as exc:
        result = failed_document(job.source_id, job.name, str(exc))
        if exc.code in {"empty_text", "unsupported_type", "encoding"}:
            result = result.model_copy(update={"read_status": "unsupported"})
    except (httpx.HTTPError, OSError):
        result = failed_document(
            job.source_id, job.name, "Không tải được nguồn: network/TLS/timeout."
        )
    sys.stdout.buffer.write(result.model_dump_json().encode("utf-8"))


if __name__ == "__main__":
    main()
