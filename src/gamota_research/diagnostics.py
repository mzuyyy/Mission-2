from datetime import datetime
from pathlib import Path

from gamota_research.contracts import Contract, utc_now
from gamota_research.errors import ResearchError
from gamota_research.llm import ChatGenerator
from gamota_research.models import Usage
from gamota_research.prompts import PROMPT_VERSION
from gamota_research.provider_errors import ProviderFailure


class FailureRecord(Contract):
    """Operational metadata only; no source text, model content, URL or credential."""

    error_code: str
    model_id: str
    prompt_version: str
    usage: Usage
    provider_failure: ProviderFailure | None
    max_requests: int
    max_output_tokens: int
    timeout_seconds: float
    timestamp: datetime


def write_failure(path: Path, error: ResearchError, generator: ChatGenerator) -> None:
    record = FailureRecord(
        error_code=error.code,
        model_id=generator.model_id,
        prompt_version=PROMPT_VERSION,
        usage=generator.usage(),
        provider_failure=generator.last_failure,
        max_requests=generator.settings.max_llm_requests_per_run,
        max_output_tokens=generator.settings.max_output_tokens,
        timeout_seconds=generator.settings.llm_timeout_seconds,
        timestamp=utc_now(),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as output:
        output.write(record.model_dump_json(indent=2))
