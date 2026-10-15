import math
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from gamota_research.errors import ResearchError

STATUS_RATE_LIMIT: Final = 429
STATUS_PAYLOAD_TOO_LARGE: Final = 413
STATUS_SERVER_ERROR_MIN: Final = 500

FailureCategory = Literal[
    "daily_quota", "upstream_capacity", "rate_limit", "payload_too_large", "http_error"
]


class ErrorMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")
    limit_source: str = ""
    raw: str = ""


class ErrorBody(BaseModel):
    model_config = ConfigDict(extra="ignore")
    message: str = ""
    metadata: ErrorMetadata = Field(default_factory=ErrorMetadata)


class ErrorEnvelope(BaseModel):
    model_config = ConfigDict(extra="ignore")
    error: ErrorBody = Field(default_factory=ErrorBody)


@dataclass(frozen=True, slots=True)
class ProviderFailure:
    """Only classified metadata can leave the transport; never raw provider text."""

    status: int
    category: FailureCategory
    retry_after_seconds: float | None

    def as_error(self) -> ResearchError:
        message = f"Provider trả HTTP {self.status}. "
        match self.category:
            case "daily_quota":
                message += "Đã hết hạn mức ngày; chờ quota reset, retry ngay không giúp. "
            case "upstream_capacity":
                message += (
                    "Pool dùng chung của model đang bị giới hạn upstream; chưa phải lỗi đọc nguồn. "
                )
            case "rate_limit":
                message += "Provider đang giới hạn tốc độ request. "
            case "payload_too_large":
                message += (
                    "Input vượt giới hạn token của gói hiện tại; giảm số nguồn/context "
                    "hoặc nâng gói dịch vụ. "
                )
            case "http_error":
                message += "Kiểm tra cấu hình hoặc trạng thái dịch vụ. "
        if self.retry_after_seconds is not None:
            message += f"Thử lại sau ít nhất {math.ceil(self.retry_after_seconds)} giây. "
        retryable = self.category != "daily_quota" and (
            self.status == STATUS_RATE_LIMIT or self.status >= STATUS_SERVER_ERROR_MIN
        )
        return ResearchError(
            "provider_retryable" if retryable else "provider_http",
            message + "Không tự đổi model/provider.",
        )


def retry_delay(header: str | None) -> float | None:
    if header is None:
        return None
    try:
        seconds = float(header)
    except ValueError:
        try:
            date = parsedate_to_datetime(header)
            if date.tzinfo is None:
                date = date.replace(tzinfo=UTC)
            seconds = (date - datetime.now(UTC)).total_seconds()
        except (ValueError, TypeError, OverflowError):
            return None
    return max(0.0, seconds) if math.isfinite(seconds) else None


def classify_failure(status: int, raw: bytes, retry_after: str | None) -> ProviderFailure:
    try:
        body = ErrorEnvelope.model_validate_json(raw).error
    except ValidationError:
        body = ErrorBody()
    category: FailureCategory = "http_error"
    if status == STATUS_RATE_LIMIT:
        detail = (body.message + " " + body.metadata.raw).casefold()
        if any(
            marker in detail for marker in ("free-models-per-day", "daily limit", "daily quota")
        ):
            category = "daily_quota"
        elif (
            body.metadata.limit_source == "upstream_provider_shared_pool"
            or "rate-limited upstream" in detail
        ):
            category = "upstream_capacity"
        else:
            category = "rate_limit"
    elif status == STATUS_PAYLOAD_TOO_LARGE:
        detail = (body.message + " " + body.metadata.raw).casefold()
        if "too large" in detail or "reduce your message size" in detail:
            category = "payload_too_large"
    return ProviderFailure(status, category, retry_delay(retry_after))
