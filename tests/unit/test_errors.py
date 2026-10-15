from collections.abc import Iterator
from contextlib import contextmanager

import pytest

from gamota_research.errors import ResearchError


def test_research_error_propagates_through_stream_context() -> None:
    @contextmanager
    def response_stream() -> Iterator[None]:
        yield

    # Given / When / Then: contextlib must be allowed to attach traceback to an exception.
    with pytest.raises(ResearchError, match="empty_text"), response_stream():
        raise ResearchError("empty_text", "Nguồn cần JS/OCR")
