from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", frozen=True)

    app_mode: Literal["live", "fixture"] = "live"
    llm_api_base: str = ""
    llm_api_key: SecretStr = SecretStr("")
    llm_model: str = ""
    llm_api_style: Literal["openai_chat"] = "openai_chat"
    llm_json_mode: bool = True
    llm_token_parameter: Literal["max_completion_tokens", "max_tokens"] = "max_completion_tokens"  # noqa: S105 -- API field name, not a credential.
    fallback_llm_api_base: str = ""
    fallback_llm_api_key: SecretStr = SecretStr("")
    fallback_llm_model: str = ""
    llm_timeout_seconds: float = Field(default=45, gt=0, le=180)
    max_sources: int = Field(default=12, ge=1, le=20)
    max_file_mb: int = Field(default=10, ge=1, le=20)
    max_pdf_pages: int = Field(default=60, ge=1, le=200)
    max_source_chars: int = Field(default=60000, ge=100, le=200000)
    max_context_chars: int = Field(default=40000, ge=500, le=100000)
    max_llm_requests_per_run: int = Field(default=4, ge=2, le=8)
    max_output_tokens: int = Field(default=2500, ge=200, le=10000)
    http_timeout_seconds: float = Field(default=20, gt=0, le=60)
    max_redirects: int = Field(default=3, ge=0, le=5)
    pdf_timeout_seconds: float = Field(default=15, gt=0, le=60)

    @property
    def live_ready(self) -> bool:
        return bool(self.llm_api_base and self.llm_api_key.get_secret_value() and self.llm_model)

    @property
    def fallback_ready(self) -> bool:
        return bool(
            self.fallback_llm_api_base
            and self.fallback_llm_api_key.get_secret_value()
            and self.fallback_llm_model
        )

    @property
    def max_bytes(self) -> int:
        return self.max_file_mb * 1024 * 1024
