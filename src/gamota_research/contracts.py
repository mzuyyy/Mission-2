from datetime import UTC, date, datetime
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")]
Provenance = Literal["user", "document", "heuristic", "model", "human", "unknown"]
AssessmentLabel = Literal["supported", "limited", "conflicting", "insufficient"]
ReviewDecision = Literal["unreviewed", "accept", "needs_review", "reject"]


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_id() -> str:
    return uuid4().hex


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=False)


class ResearchRequest(Contract):
    request_id: Identifier = Field(default_factory=new_id)
    question: str = Field(min_length=5, max_length=4000)
    country: list[str] = Field(min_length=1, max_length=1)
    platforms: list[str] = Field(min_length=1, max_length=8)
    period_start: date | None = None
    period_end: date | None = None
    decision_goal: str = Field(min_length=1, max_length=200)
    alternatives: list[str] = Field(default_factory=list, max_length=8)
    constraints: list[str] = Field(default_factory=list, max_length=12)
    clarified: bool = False
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def valid_period(self) -> "ResearchRequest":
        if self.period_start and self.period_end and self.period_start > self.period_end:
            raise ValueError("period_start phải trước period_end")
        if not self.question.strip() or not all(x.strip() for x in self.country + self.platforms):
            raise ValueError("Câu hỏi và phạm vi không được để trống")
        return self


class PageRange(Contract):
    page_number: int = Field(ge=1)
    start_char: int = Field(ge=0)
    end_char: int = Field(ge=0)


class SourceDocument(Contract):
    source_id: Identifier
    display_title: str
    original_url: str | None = None
    local_name: str | None = None
    content_hash: str
    normalized_text: str
    retrieved_at: datetime = Field(default_factory=utc_now)
    published_at: date | None = None
    data_period: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    country: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)
    publisher: str | None = None
    source_kind: Literal[
        "original_report", "company_disclosure", "syndication", "opinion", "unknown"
    ] = "unknown"
    original_root_id: str | None = None
    root_relation_reason: str = "Chưa xác định quan hệ với nguồn gốc."
    metadata_provenance: dict[str, Provenance] = Field(default_factory=dict)
    methodology: str | None = None
    conflicts_of_interest: str | None = None
    read_status: Literal["ok", "partial", "failed", "unsupported"] = "ok"
    read_error: str | None = None
    is_synthetic: bool = False
    permission_note: str = (
        "Nguồn công khai do người dùng cung cấp; chưa xác nhận quyền tái phân phối."
    )
    pages: list[PageRange] = Field(default_factory=list)


class Dimension(Contract):
    value: Literal["yes", "no", "partial", "unknown"] = "unknown"
    rationale: str
    provenance: Provenance = "heuristic"


class SourceAssessment(Contract):
    source_id: Identifier
    claim_or_question_id: Identifier
    origin: Dimension
    methodology: Dimension
    scope: Dimension
    freshness: Dimension
    interest: Dimension
    independence: Dimension
    summary_label: Literal["strong_for_this_claim", "limited", "unsuitable", "unknown"]


class Evidence(Contract):
    evidence_id: Identifier
    source_id: Identifier
    content_hash: str
    quote: str = Field(min_length=1, max_length=6000)
    start_char: int = Field(ge=0)
    end_char: int = Field(gt=0)
    page_number: int | None = None
    section: str | None = None
    surrounding_context: str
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


class EvidenceLink(Contract):
    evidence_id: Identifier
    relation: Literal["supports", "contradicts", "context"]


class Claim(Contract):
    claim_id: Identifier
    text: str = Field(min_length=1, max_length=4000)
    kind: Literal["fact", "inference", "hypothesis"]
    material: bool = True
    assessment: AssessmentLabel = "insufficient"
    evidence_links: list[EvidenceLink] = Field(default_factory=list)
    premise_claim_ids: list[Identifier] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    reasoning: str | None = None
    missing_data: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    human_review: ReviewDecision = "unreviewed"


class ComparisonDimensions(Contract):
    subject: str | None = None
    country: str | None = None
    platform: str | None = None
    period: str | None = None
    metric: str | None = None
    unit: str | None = None
    currency: str | None = None
    gross_net: str | None = None
    actual_or_estimate: str | None = None


class Conflict(Contract):
    conflict_id: Identifier
    claim_ids: list[Identifier]
    evidence_ids: list[Identifier] = Field(min_length=2)
    comparison_dimensions: ComparisonDimensions
    same_scope: bool | Literal["unknown"] = "unknown"
    explanation: str
    unresolved: bool = True
    affected_recommendation_ids: list[Identifier] = Field(default_factory=list)


class Recommendation(Contract):
    recommendation_id: Identifier
    action: str
    rationale: str
    premise_claim_ids: list[Identifier] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    blocking_unknowns: list[str] = Field(default_factory=list)
    blocked: bool = True
    next_step: str = Field(min_length=1)
    owner_role: str | None = None
