import json
import time
from http import HTTPStatus
from typing import Final, Protocol, TypeVar
from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel, ConfigDict, Field, JsonValue, ValidationError

from gamota_research.config import Settings
from gamota_research.errors import ResearchError
from gamota_research.models import Usage
from gamota_research.prompts import SYSTEM
from gamota_research.provider_errors import ProviderFailure, classify_failure

T = TypeVar("T", bound=BaseModel)
MAX_RESPONSE_BYTES: Final = 2_000_000
MAX_RETRY_DELAY_SECONDS: Final = 30


class Generator(Protocol):
    @property
    def model_id(self) -> str: ...

    def generate(self, schema: type[T], instructions: str, payload: str) -> T: ...

    def usage(self) -> Usage: ...


class ApiMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    content: str | None = None
    refusal: str | None = None


class ApiChoice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    message: ApiMessage
    finish_reason: str


class ApiUsage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    total_tokens: int = Field(ge=0)


class ApiResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    choices: list[ApiChoice] = Field(min_length=1)
    usage: ApiUsage | None = None


class ChatGenerator:
    """One configured endpoint/model; mutable counters include every retry and repair."""

    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None) -> None:
        if not settings.live_ready:
            raise ResearchError(
                "llm_not_configured", "Cấu hình API base/model/key tại máy; không gửi key vào chat."
            )
        parsed = urlsplit(settings.llm_api_base)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ResearchError(
                "llm_config", "API base cần HTTPS, không credentials/query/fragment."
            )
        self.settings = settings
        self.transport = transport
        self.request_count = 0
        self.total_tokens = 0
        self.tokens_known = True
        self.started = time.monotonic()
        self.last_failure: ProviderFailure | None = None
        self.using_fallback = False
        if settings.fallback_ready:
            self._check_base(settings.fallback_llm_api_base)

    @staticmethod
    def _check_base(base: str) -> None:
        parsed = urlsplit(base)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ResearchError(
                "llm_config", "Fallback API base cần HTTPS, không credentials/query/fragment."
            )

    def _endpoint(self) -> tuple[str, str, str]:
        """Active (base, key, model); fallback after primary is rate-limited."""
        if self.using_fallback:
            return (
                self.settings.fallback_llm_api_base,
                self.settings.fallback_llm_api_key.get_secret_value(),
                self.settings.fallback_llm_model,
            )
        return (
            self.settings.llm_api_base,
            self.settings.llm_api_key.get_secret_value(),
            self.settings.llm_model,
        )

    @property
    def model_id(self) -> str:
        return self._endpoint()[2]

    def usage(self) -> Usage:
        return Usage(
            request_count=self.request_count,
            tokens=self.total_tokens if self.tokens_known else None,
            latency_ms=int((time.monotonic() - self.started) * 1000),
        )

    def generate(self, schema: type[T], instructions: str, payload: str) -> T:
        schema_json = json.dumps(schema.model_json_schema(), ensure_ascii=False)
        repair = ""
        for attempt in range(2):
            if self.request_count >= self.settings.max_llm_requests_per_run:
                raise ResearchError(
                    "request_budget", "Đã hết ngân sách request (gồm retry/repair)."
                )
            self.request_count += 1
            body = self._body(schema_json, instructions, payload, repair)
            try:
                parsed = self._request(body)
                return schema.model_validate_json(self._content(parsed))
            except ResearchError as exc:
                if not self._should_retry_provider_error(exc, attempt):
                    raise
                if exc.code == "provider_incomplete":
                    repair = (
                        "\nOutput trước không hoàn tất. Rút gọn JSON để vừa cùng ngân sách: "
                        "ít mục hơn, bỏ field tùy chọn/null, không chép lại quote. "
                        "Không bỏ qua phản chứng hoặc giả vờ đã đủ dữ liệu."
                    )
            except ValidationError as exc:
                if attempt:
                    raise ResearchError(
                        "provider_json", "JSON không đúng schema sau một lần sửa."
                    ) from exc
                repair = "\nLượt trước JSON sai schema. Tạo lại JSON hợp lệ, giữ unknown, không bịa dữ liệu."
            except httpx.HTTPError as exc:
                self.tokens_known = False
                if attempt:
                    raise ResearchError(
                        "provider_network", "Provider network/timeout; không đổi provider."
                    ) from exc
                time.sleep(0.5)
        raise ResearchError("provider_json", "Không nhận JSON hợp lệ trong ngân sách.")

    def _should_retry_provider_error(self, exc: ResearchError, attempt: int) -> bool:
        """One bounded retry for transient provider errors, inside the shared budget.

        provider_retryable switches to the configured fallback endpoint once
        (no sleep: different provider, different quota) instead of waiting out
        the primary delay; without fallback it waits as before. provider_incomplete
        (refusal/truncated output) retries immediately. Never fabricates output.
        """
        if attempt or exc.code not in ("provider_retryable", "provider_incomplete"):
            return False
        if exc.code == "provider_retryable" and self._switch_to_fallback():
            return True
        if exc.code == "provider_retryable":
            delay = self._retry_delay()
            if delay > MAX_RETRY_DELAY_SECONDS:
                return False
            time.sleep(delay)
        return True

    def _switch_to_fallback(self) -> bool:
        """Use the fallback endpoint once per generator; report via model_id."""
        if self.using_fallback or not self.settings.fallback_ready:
            return False
        self.using_fallback = True
        return True

    def _retry_delay(self) -> float:
        failure = self.last_failure
        if failure is None or failure.retry_after_seconds is None:
            return 2.0
        return max(0.5, failure.retry_after_seconds)

    def _body(
        self, schema_json: str, instructions: str, payload: str, repair: str
    ) -> dict[str, JsonValue]:
        _, _, model = self._endpoint()
        body: dict[str, JsonValue] = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM + instructions + "\nJSON schema:\n" + schema_json + repair,
                },
                {"role": "user", "content": payload},
            ],
            self.settings.llm_token_parameter: self.settings.max_output_tokens,
        }
        if self.settings.llm_json_mode:
            body["response_format"] = {"type": "json_object"}
        return body

    def _request(self, body: dict[str, JsonValue]) -> ApiResponse:
        self.last_failure = None
        base, key, _ = self._endpoint()
        transport = self.transport or httpx.HTTPTransport(retries=0, trust_env=False)
        deadline = time.monotonic() + self.settings.llm_timeout_seconds
        with (
            httpx.Client(
                transport=transport,
                timeout=self.settings.llm_timeout_seconds,
                follow_redirects=False,
                trust_env=False,
            ) as client,
            client.stream(
                "POST",
                base.rstrip("/") + "/chat/completions",
                headers={"Authorization": "Bearer " + key},
                json=body,
            ) as response,
        ):
            status = response.status_code
            raw = bytearray()
            for chunk in response.iter_bytes():
                if time.monotonic() > deadline:
                    raise ResearchError("provider_timeout", "Provider vượt thời gian request.")
                if len(raw) + len(chunk) > MAX_RESPONSE_BYTES:
                    raise ResearchError("provider_size", "Provider response vượt giới hạn.")
                raw.extend(chunk)
            if status != HTTPStatus.OK:
                self.tokens_known = False
                self.last_failure = classify_failure(
                    status, bytes(raw), response.headers.get("retry-after")
                )
                raise self.last_failure.as_error()
        return ApiResponse.model_validate_json(bytes(raw))

    def _content(self, parsed: ApiResponse) -> str:
        if parsed.usage is None:
            self.tokens_known = False
        else:
            self.total_tokens += parsed.usage.total_tokens
        choice = parsed.choices[0]
        if choice.message.refusal or choice.finish_reason != "stop" or not choice.message.content:
            raise ResearchError(
                "provider_incomplete",
                "Provider từ chối hoặc output bị cắt; không tạo report mẫu.",
            )
        return choice.message.content
