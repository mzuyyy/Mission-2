from typing import Literal

from gamota_research.contracts import (
    Claim,
    ComparisonDimensions,
    Evidence,
)
from gamota_research.errors import ResearchError


def unique_ids(ids: list[str], label: str) -> None:
    if len(ids) != len(set(ids)):
        raise ResearchError("duplicate_id", f"ID trùng trong {label}.")


def compare_evidence(
    items: list[Evidence],
) -> tuple[bool | Literal["unknown"], ComparisonDimensions]:
    fields = ComparisonDimensions.model_fields
    dimensions: dict[str, str | None] = {}
    different = False
    unknown = False
    for field in fields:
        values = [item.model_dump()[field] for item in items]
        known = {value.casefold().strip() for value in values if isinstance(value, str)}
        if len(known) > 1:
            different = True
        if len(known) == 0 or any(value is None for value in values):
            unknown = True
        dimensions[field] = next(iter(known)) if len(known) == 1 else None
    same: bool | Literal["unknown"] = False if different else ("unknown" if unknown else True)
    return same, ComparisonDimensions.model_validate(dimensions)


def check_graph(claims: list[Claim]) -> None:
    by_id = {c.claim_id: c for c in claims}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(cid: str) -> None:
        if cid in visiting:
            raise ResearchError("premise_cycle", "Vòng lặp trong premise IDs.")
        if cid in visited:
            return
        visiting.add(cid)
        for parent in by_id[cid].premise_claim_ids:
            if parent not in by_id:
                raise ResearchError("dangling_id", f"{cid}: premise ID không tồn tại.")
            visit(parent)
        visiting.remove(cid)
        visited.add(cid)

    for cid in by_id:
        visit(cid)
