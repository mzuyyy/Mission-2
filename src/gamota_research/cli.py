import io
import json
import sys
from pathlib import Path
from typing import Annotated, Final

import typer
from pydantic import TypeAdapter, ValidationError

from gamota_research.config import Settings
from gamota_research.contracts import ResearchRequest, SourceDocument
from gamota_research.diagnostics import write_failure
from gamota_research.errors import ResearchError
from gamota_research.export import export_markdown
from gamota_research.fixtures import load_fixtures
from gamota_research.ingestion.pdf import parse_pdf
from gamota_research.ingestion.public_url import fetch_public
from gamota_research.llm import ChatGenerator
from gamota_research.pipeline import run_research
from gamota_research.retrieval import retrieve
from gamota_research.storage import load_bundle

app = typer.Typer(
    help="Gamota research: ingestion, live generation and replay.",
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
)
sources_adapter = TypeAdapter(list[SourceDocument])
MAX_REQUEST_BYTES: Final = 50000
MAX_BUNDLE_BYTES: Final = 30_000_000


@app.callback()
def utf8_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")


def write_output(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as output:
        output.write(text)


def load_sources(path: Path, settings: Settings) -> list[SourceDocument]:
    if path.stat().st_size > settings.max_sources * settings.max_source_chars * 8 + 100000:
        raise ResearchError("source_size", "Snapshot JSON vượt giới hạn.")
    sources = sources_adapter.validate_json(path.read_bytes())
    if len(sources) > settings.max_sources:
        raise ResearchError("source_limit", "Vượt số nguồn tối đa.")
    return sources


def fail(error: ResearchError | ValidationError | OSError) -> None:
    typer.echo(
        str(error)
        if isinstance(error, ResearchError)
        else "Input/file không hợp lệ; kiểm tra schema, đường dẫn và quyền ghi.",
        err=True,
    )
    raise typer.Exit(code=2)


@app.command()
def ingest(
    out: Annotated[Path, typer.Option()],
    url: list[str] | None = None,
    pdf: list[Path] | None = None,
) -> None:
    """Read public URLs and local text PDFs without an API key."""
    try:
        settings = Settings()
        urls, pdfs = url or [], pdf or []
        if len(urls) + len(pdfs) > settings.max_sources:
            raise ResearchError("source_limit", "Vượt số nguồn tối đa.")
        sources = [fetch_public(item, f"U{index}", settings) for index, item in enumerate(urls, 1)]
        for index, path in enumerate(pdfs, 1):
            if path.stat().st_size > settings.max_bytes:
                raise ResearchError("file_size", "PDF vượt giới hạn dung lượng.")
            sources.append(parse_pdf(path.read_bytes(), f"P{index}", path.name, settings))
        write_output(out, sources_adapter.dump_json(sources, indent=2).decode("utf-8"))
        for source in sources:
            typer.echo(
                f"{source.source_id}: {source.read_status}; chars={len(source.normalized_text)}"
            )
    except (ResearchError, ValidationError, OSError) as error:
        fail(error)


@app.command()
def fixtures(out: Annotated[Path, typer.Option()]) -> None:
    """Export explicitly synthetic source snapshots for offline inspection or live logic evaluation."""
    try:
        sources = load_fixtures(Path("data/fixtures"))
        write_output(out, sources_adapter.dump_json(sources, indent=2).decode("utf-8"))
        typer.echo("DỮ LIỆU GIẢ LẬP, không phải kết quả nghiên cứu thị trường.")
    except (ResearchError, ValidationError, OSError) as error:
        fail(error)


@app.command()
def run(
    request: Annotated[Path, typer.Option()],
    sources: Annotated[Path, typer.Option()],
    out: Annotated[Path, typer.Option()],
) -> None:
    """Generate through the same two-stage pipeline as the UI. Never falls back to mock."""
    generator: ChatGenerator | None = None
    try:
        settings = Settings()
        if request.stat().st_size > MAX_REQUEST_BYTES:
            raise ResearchError("request_size", "Request JSON vượt giới hạn.")
        research_request = ResearchRequest.model_validate_json(request.read_bytes())
        documents = load_sources(sources, settings)
        generator = ChatGenerator(settings)
        bundle = run_research(research_request, documents, generator, settings)
        write_output(out, bundle.model_dump_json(indent=2))
        write_output(out.with_suffix(".md"), export_markdown(bundle))
        typer.echo(f"{bundle.report.mode}: {len(bundle.report.claims)} claims; {out}")
    except ResearchError as error:
        if generator is not None:
            try:
                write_failure(out.with_suffix(".failure.json"), error, generator)
            except OSError:
                typer.echo("Không ghi được failure artifact; giữ nguyên file có sẵn.", err=True)
        fail(error)
    except (ValidationError, OSError) as error:
        fail(error)


@app.command()
def inspect(
    request: Annotated[Path, typer.Option()],
    sources: Annotated[Path, typer.Option()],
    out: Annotated[Path, typer.Option()],
) -> None:
    """Inspect selected source spans and coverage offline; this produces no AI claims."""
    try:
        settings = Settings()
        if request.stat().st_size > MAX_REQUEST_BYTES:
            raise ResearchError("request_size", "Request JSON vượt giới hạn.")
        research_request = ResearchRequest.model_validate_json(request.read_bytes())
        documents = load_sources(sources, settings)
        spans, coverage = retrieve(research_request, documents, settings.max_context_chars)
        write_output(
            out,
            json.dumps(
                {
                    "mode": "offline_inspection",
                    "claims_generated": False,
                    "coverage": coverage.model_dump(),
                    "spans": [s.model_dump() for s in spans],
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
        typer.echo(f"Offline: {len(spans)} spans; không có nhận định LLM.")
    except (ResearchError, ValidationError, OSError) as error:
        fail(error)


@app.command()
def replay(bundle: Annotated[Path, typer.Option()], out: Annotated[Path, typer.Option()]) -> None:
    """Validate a saved JSON bundle and export it with a replay label."""
    try:
        if bundle.stat().st_size > MAX_BUNDLE_BYTES:
            raise ResearchError("replay_size", "Bundle vượt giới hạn.")
        saved = load_bundle(bundle.read_bytes())
        write_output(out, export_markdown(saved))
        typer.echo("REPLAY: kết quả đã lưu, không gọi LLM.")
    except (ResearchError, ValidationError, OSError) as error:
        fail(error)


if __name__ == "__main__":
    app()
