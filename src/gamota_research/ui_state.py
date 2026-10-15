from dataclasses import dataclass, field

import streamlit as st

from gamota_research.contracts import ResearchRequest, SourceDocument
from gamota_research.models import ReportBundle
from gamota_research.storage import Workspace


@dataclass(slots=True)
class Session:
    """Mutable state belongs to exactly one Streamlit session, never a global cache."""

    workspace: Workspace = field(default_factory=Workspace)
    sources: list[SourceDocument] = field(default_factory=list)
    bundle: ReportBundle | None = None
    request: ResearchRequest | None = None


def current_session() -> Session:
    stored = st.session_state.get("research_session")
    if isinstance(stored, Session):
        return stored
    session = Session()
    st.session_state["research_session"] = session
    return session
