from io import BytesIO

from reportlab.lib.pagesizes import landscape
from reportlab.pdfgen.canvas import Canvas

from gamota_research.config import Settings
from gamota_research.contracts import PageRange, ResearchRequest
from gamota_research.ingestion.isolation import IngestLimits
from gamota_research.ingestion.normalize import document
from gamota_research.ingestion.pdf import parse_pdf_inner
from gamota_research.retrieval import retrieve, split_spans


def test_pdf_columns_follow_positions_instead_of_drawing_order() -> None:
    output = BytesIO()
    canvas = Canvas(output, pagesize=landscape((600, 840)))
    canvas.drawString(40, 550, "Synthetic company results FY 2031")
    for x, title, metric in [
        (40, "Alpha", "Revenue"),
        (310, "Beta", "Loans"),
        (580, "Gamma", "Bookings"),
    ]:
        canvas.drawString(x, 500, title)
        canvas.drawString(x, 480, metric)
        canvas.drawString(x, 460, "USD billions")
    # PDF drawing order differs from visual order, as in the observed source bug.
    for x, value in [(310, "8.4"), (580, "2.7"), (40, "3.1")]:
        canvas.drawString(x, 420, value)
        canvas.drawString(x, 400, "FY 2031")
    canvas.save()
    source = parse_pdf_inner(
        output.getvalue(), "S1", "synthetic.pdf", IngestLimits.from_settings(Settings())
    )
    row = next(line for line in source.normalized_text.splitlines() if "3.1" in line)
    assert "8.4" in row
    assert "2.7" in row
    assert row.index("3.1") < row.index("8.4") < row.index("2.7")
    headings = next(line for line in source.normalized_text.splitlines() if "Alpha" in line)
    assert headings.index("Alpha") < headings.index("Beta") < headings.index("Gamma")
    assert source.read_status == "ok"


def test_pdf_page_keeps_headers_and_values_in_one_exact_span() -> None:
    text = "Synthetic FY 2031\n" + "Row with explanatory text.\n" * 65 + "Gamma Bookings 2.7\n"
    source = document("S1", "Synthetic PDF", text).model_copy(
        update={"pages": [PageRange(page_number=1, start_char=0, end_char=len(text))]}
    )
    spans = split_spans(source)
    assert len(spans) == 1
    assert spans[0].text == text
    assert spans[0].page_number == 1
    assert source.normalized_text[spans[0].start_char : spans[0].end_char] == text


def test_layout_keeps_rotated_text_instead_of_silently_dropping_it() -> None:
    output = BytesIO()
    canvas = Canvas(output)
    canvas.drawString(40, 700, "Synthetic results")
    canvas.saveState()
    canvas.translate(100, 100)
    canvas.rotate(90)
    canvas.drawString(0, 0, "Important rotated caveat")
    canvas.restoreState()
    canvas.save()
    source = parse_pdf_inner(
        output.getvalue(), "S1", "rotated.pdf", IngestLimits.from_settings(Settings())
    )
    assert "Important rotated caveat" in source.normalized_text


def test_oversized_pdf_page_is_omitted_instead_of_sending_orphan_numbers() -> None:
    text = "Table header FY 2031\n" + "Narrative context.\n" * 350 + "Bookings 2.7\n"
    source = document("S1", "Synthetic PDF", text).model_copy(
        update={"pages": [PageRange(page_number=1, start_char=0, end_char=len(text))]}
    )
    request = ResearchRequest(
        question="What do Bookings show?",
        country=["unknown"],
        platforms=["unknown"],
        decision_goal="competition",
        clarified=True,
    )
    selected, coverage = retrieve(request, [source], 8000)
    assert selected == []
    assert coverage.context_truncated
    assert len(coverage.omitted_span_ids) == 1
    assert any("PDF" in warning for warning in coverage.warnings)


def test_text_sources_keep_normal_chunking() -> None:
    source = document("S1", "HTML", "Paragraph.\n" * 300)
    spans = split_spans(source)
    assert len(spans) > 1
    assert "".join(span.text for span in spans) == source.normalized_text
