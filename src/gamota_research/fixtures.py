from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from gamota_research.contracts import SourceDocument
from gamota_research.errors import ResearchError
from gamota_research.ingestion.normalize import document


class FixtureEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    source_id: str
    title: str
    path: str
    source_kind: Literal[
        "original_report", "company_disclosure", "syndication", "opinion", "unknown"
    ]
    publisher: str | None = None
    country: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)
    data_period: str | None = None
    original_root_id: str | None = None
    root_relation_reason: str
    published_at: str | None = None
    permission_note: str


class Manifest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    is_synthetic: Literal[True]
    sources: list[FixtureEntry]


def load_fixtures(
    root: Path, source_ids: list[str] | None = None, max_chars: int = 60000
) -> list[SourceDocument]:
    """Load only the synthetic source manifest; never evaluation cases or expected answers."""
    manifest = Manifest.model_validate_json((root / "manifest.json").read_bytes())
    sources: list[SourceDocument] = []
    for entry in manifest.sources:
        if source_ids is not None and entry.source_id not in source_ids:
            continue
        path = (root / entry.path).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ResearchError("fixture_path", "Đường dẫn fixture nằm ngoài thư mục nguồn.")
        source = document(entry.source_id, entry.title, path.read_text(encoding="utf-8"), max_chars)
        metadata = entry.model_dump(exclude={"path", "title"})
        combined = {
            **source.model_dump(),
            **metadata,
            "is_synthetic": True,
            "metadata_provenance": dict.fromkeys(metadata, "document"),
        }
        sources.append(SourceDocument.model_validate(combined))
    if source_ids is not None and set(source_ids) - {s.source_id for s in sources}:
        raise ResearchError("fixture_source", "Source ID không tồn tại trong manifest.")
    return sources
