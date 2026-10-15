"""Evaluator-only contracts and measurements. Never imported by src/app."""

import hashlib
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from gamota_research.contracts import ResearchRequest, utc_now
from gamota_research.models import ReportBundle
from gamota_research.prompts import PROMPT_VERSION


class CaseInput(BaseModel):
    model_config = ConfigDict(extra="ignore")
    question: str
    country: list[str]
    platforms: list[str]
    period_start: str | None = None
    period_end: str | None = None
    decision_goal: str
    source_ids: list[str] = Field(default_factory=list)
    urls: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)

    def research_request(self) -> ResearchRequest:
        return ResearchRequest.model_validate(
            {**self.model_dump(exclude={"source_ids", "urls"}), "clarified": True}
        )


class Case(BaseModel):
    model_config = ConfigDict(extra="ignore")
    case_id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    split: str
    category: str
    input: CaseInput
    expected_file: str | None = None
    expected: str | None = None


class Dataset(BaseModel):
    model_config = ConfigDict(extra="ignore")
    is_synthetic: bool
    cases: list[Case]


class EvaluationResult(BaseModel):
    run_id: str
    case_id: str
    split: str
    input_hashes: dict[str, str]
    code_revision: str
    model_id: str | None
    prompt_version: str = PROMPT_VERSION
    actual_output_path: str | None = None
    expected: JsonValue
    actual: str
    verdict: Literal["NOT_RUN", "PASS", "FAIL", "BLOCKED"]
    learned: str
    timestamp: datetime = Field(default_factory=utc_now)
    reviewer: str = "automated_locator_checks_only"
    checks: dict[str, JsonValue]
    live_or_mock: str = "live_attempt_no_mock"


def code_revision() -> str:
    hasher = hashlib.sha256()
    for path in sorted(
        [Path("app.py"), Path("pyproject.toml"), Path("uv.lock"), *Path("src").rglob("*.py")]
    ):
        hasher.update(path.as_posix().encode())
        hasher.update(path.read_bytes())
    return "no_git_snapshot_sha256:" + hasher.hexdigest()


def prompt_hash() -> str:
    return hashlib.sha256(Path("src/gamota_research/prompts.py").read_bytes()).hexdigest()


def failure_verdict(actual: str, *, live_ready: bool) -> Literal["BLOCKED", "FAIL"]:
    blocked_codes = {
        "llm_not_configured",
        "llm_config",
        "provider_network",
        "provider_timeout",
        "provider_http",
        "provider_retryable",
        "evaluation_timeout",
    }
    code = actual.strip().split(":", 1)[0]
    return "BLOCKED" if not live_ready or code in blocked_codes else "FAIL"


def run_cli(command: list[str], timeout: float) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(  # noqa: S603 -- fixed interpreter/module argv from evaluator; no shell.
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            command, 124, "", "evaluation_timeout: CLI exceeded wall-clock deadline"
        )


def automatic_checks(bundle: ReportBundle) -> dict[str, JsonValue]:
    # load_bundle already checks hash/quote/page/IDs. Semantics remain unanswered.
    total = len(bundle.report.evidence)
    material = sum(c.kind == "fact" and c.material for c in bundle.report.claims)
    return {
        "citation_matches": total,
        "citation_total": total,
        "citation_ratio": total / total if total else None,
        "material_facts_total": material,
        "material_supported_by_human": None,
        "material_support_ratio": None,
        "unsupported_material_count": None,
        "missed_conflicts": None,
        "semantic_review": "NOT_RUN",
        "completeness_review": "NOT_RUN",
    }
