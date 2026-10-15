import re
import unicodedata
from collections import deque

from gamota_research.contracts import ResearchRequest, SourceDocument
from gamota_research.models import Coverage, Span


def tokens(text: str) -> set[str]:
    folded = "".join(
        c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn"
    ).replace("đ", "d")
    return set(re.findall(r"[a-z0-9]+", folded))


def split_spans(source: SourceDocument, size: int = 1400) -> list[Span]:
    spans: list[Span] = []
    ranges = [(page.start_char, page.end_char, page.page_number) for page in source.pages]
    if not ranges:
        ranges = [(0, len(source.normalized_text), None)]
    for start, end, page in ranges:
        position = start
        while position < end:
            stop = min(position + size, end)
            if stop < end:
                boundary = source.normalized_text.rfind("\n", position + size // 2, stop)
                if boundary > position:
                    stop = boundary + 1
            text = source.normalized_text[position:stop]
            if text.strip():
                spans.append(
                    Span(
                        span_id=f"{source.source_id}_{position}_{stop}",
                        source_id=source.source_id,
                        start_char=position,
                        end_char=stop,
                        text=text,
                        page_number=page,
                    )
                )
            position = stop
    return spans


def retrieve(
    request: ResearchRequest, sources: list[SourceDocument], max_chars: int
) -> tuple[list[Span], Coverage]:
    """Lexical ranking plus source diversity and caveat cues; omissions are always exposed."""
    all_spans = [span for source in sources for span in split_spans(source)]
    query = tokens(
        " ".join(
            [
                request.question,
                *request.country,
                *request.platforms,
                request.decision_goal,
                *request.constraints,
            ]
        )
    )
    caveats = tokens(
        "however limitation decline uncertainty missing giảm thiếu nhưng hạn chế không"
    )
    ranked: list[deque[Span]] = []
    for source in sources:
        candidates = [span for span in all_spans if span.source_id == source.source_id]
        candidates.sort(
            key=lambda s: len(tokens(s.text) & query) + 2 * len(tokens(s.text) & caveats),
            reverse=True,
        )
        ranked.append(deque(candidates))
    selected: list[Span] = []
    used = 0
    while any(ranked):
        for queue in ranked:
            if not queue:
                continue
            span = queue.popleft()
            if used + len(span.text) <= max_chars:
                selected.append(span)
                used += len(span.text)
    selected_ids = {span.span_id for span in selected}
    omitted = [span.span_id for span in all_spans if span.span_id not in selected_ids]
    warnings = [f"{s.source_id}: {s.read_error}" for s in sources if s.read_error]
    if omitted:
        warnings.append("Context không chứa toàn bộ snapshot; có thể bỏ sót phản chứng quyết định.")
    coverage = Coverage(
        read_sources=[s.source_id for s in sources if s.normalized_text],
        failed_sources=[s.source_id for s in sources if s.read_status in {"failed", "unsupported"}],
        partial_sources=[s.source_id for s in sources if s.read_status == "partial"],
        context_truncated=bool(omitted),
        omitted_span_ids=omitted,
        selected_span_ids=[s.span_id for s in selected],
        selected_chars=used,
        warnings=warnings,
    )
    return selected, coverage
