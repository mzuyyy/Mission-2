from datetime import datetime
from typing import Literal

from pydantic import Field

from gamota_research.contracts import (
    Claim,
    Conflict,
    Contract,
    Evidence,
    Identifier,
    Recommendation,
    ResearchRequest,
    ReviewDecision,
    SourceAssessment,
    SourceDocument,
    new_id,
    utc_now,
)


class Span(Contract):
    span_id: Identifier
    source_id: Identifier
    start_char: int
    end_char: int
    text: str
    page_number: int | None = None


class Coverage(Contract):
    read_sources: list[Identifier] = Field(default_factory=list)
    failed_sources: list[Identifier] = Field(default_factory=list)
    partial_sources: list[Identifier] = Field(default_factory=list)
    context_truncated: bool = False
    omitted_span_ids: list[Identifier] = Field(default_factory=list)
    selected_span_ids: list[Identifier] = Field(default_factory=list)
    selected_chars: int = 0
    warnings: list[str] = Field(default_factory=list)


class Usage(Contract):
    request_count: int = 0
    tokens: int | None = None
    estimated_cost: float | None = None
    latency_ms: int = 0


class ValidationResult(Contract):
    quote_checks: int = 0
    dangling_ids: int = 0
    failures: list[str] = Field(default_factory=list)
    semantic_support: Literal["human_review_required"] = "human_review_required"


class ReviewEvent(Contract):
    event_id: Identifier = Field(default_factory=new_id)
    report_id: Identifier
    claim_id: Identifier | None = None
    previous_version: int
    new_version: int
    decision: ReviewDecision
    note: str
    previous_claim: Claim | None = None
    new_claim: Claim | None = None
    timestamp: datetime = Field(default_factory=utc_now)


class ResearchReport(Contract):
    schema_version: Literal["1.0"] = "1.0"
    report_id: Identifier = Field(default_factory=new_id)
    request: ResearchRequest
    source_ids: list[Identifier]
    assessments: list[SourceAssessment]
    evidence: list[Evidence]
    claims: list[Claim]
    conflicts: list[Conflict]
    recommendations: list[Recommendation]
    missing_data: list[str]
    coverage: Coverage
    is_synthetic: bool
    mode: Literal["live", "fixture", "replay"]
    generated_at: datetime = Field(default_factory=utc_now)
    model_id: str | None = None
    prompt_version: str
    source_hashes: dict[str, str]
    usage: Usage
    validation: ValidationResult
    review_history: list[ReviewEvent] = Field(default_factory=list)
    version: int = Field(default=1, ge=1)


class ReportBundle(Contract):
    report: ResearchReport
    sources: list[SourceDocument]


class EvidenceDraft(Contract):
    evidence_id: Identifier
    source_id: Identifier
    span_id: Identifier
    quote: str | None = Field(default=None, min_length=1, max_length=6000)
    metric: str | None = None
    value: float | None = Field(default=None, allow_inf_nan=False)
    unit: str | None = None
    currency: str | None = None
    country: str | None = None
    platform: str | None = None
    period: str | None = None
    gross_net: str | None = None
    actual_or_estimate: str | None = None
    subject: str | None = None


class Extraction(Contract):
    evidence: list[EvidenceDraft] = Field(max_length=60)
    missing_data: list[str] = Field(default_factory=list)


class Synthesis(Contract):
    claims: list[Claim] = Field(max_length=30)
    conflicts: list[Conflict] = Field(max_length=30)
    recommendations: list[Recommendation] = Field(max_length=12)
    missing_data: list[str]
