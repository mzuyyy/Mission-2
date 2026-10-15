# /// script
# requires-python = ">=3.11"
# dependencies = ["typer", "pydantic"]
# ///
# Run in the locked project environment: uv run python eval/run_evaluation.py --help
"""Evaluation harness only. Expected labels never enter the generation subprocess."""

import json
import sys
from pathlib import Path
from typing import Annotated

import typer
from evaluation_support import (
    Case,
    Dataset,
    EvaluationResult,
    automatic_checks,
    code_revision,
    failure_verdict,
    prompt_hash,
    run_cli,
)
from pydantic import JsonValue, TypeAdapter

from gamota_research.cli import sources_adapter
from gamota_research.config import Settings
from gamota_research.contracts import new_id, utc_now
from gamota_research.diagnostics import FailureRecord
from gamota_research.fixtures import load_fixtures
from gamota_research.ingestion.public_url import fetch_public
from gamota_research.prompts import PROMPT_VERSION
from gamota_research.retrieval import retrieve
from gamota_research.storage import load_bundle

app = typer.Typer(pretty_exceptions_show_locals=False)


def load_expected(case: Case, cases: Path) -> JsonValue:
    """Freeze expectation separately before CLI execution. No evaluator data goes to CLI."""
    if not case.expected_file:
        return case.expected
    expected_path = (cases.parent / case.expected_file).resolve()
    if not expected_path.is_relative_to(cases.parent.resolve()):
        raise typer.BadParameter("Expected file nằm ngoài thư mục eval.")
    return TypeAdapter(JsonValue).validate_json(expected_path.read_bytes())


@app.command()
def main(
    cases: Annotated[Path, typer.Option()] = Path("eval/cases.json"),
    split: Annotated[str, typer.Option()] = "dev",
    output: Annotated[Path, typer.Option()] = Path("eval/runs"),
    freeze_prompt: Annotated[bool, typer.Option()] = False,
) -> None:
    settings = Settings()
    dataset = Dataset.model_validate_json(cases.read_bytes())
    revision = code_revision()
    freeze = Path("eval/prompt_freeze.json")
    current = {"prompt_version": PROMPT_VERSION, "sha256": prompt_hash()}
    if freeze_prompt:
        freeze.write_text(
            json.dumps({**current, "frozen_at": utc_now().isoformat()}, indent=2), encoding="utf-8"
        )
    if split in {"reserved", "all"}:
        if not freeze.exists():
            raise typer.BadParameter("Reserved cần --freeze-prompt trước khi chạy.")
        saved = json.loads(freeze.read_text(encoding="utf-8"))
        if any(saved.get(key) != value for key, value in current.items()):
            raise typer.BadParameter(
                "Prompt đã đổi sau freeze; cần đóng băng lại và công bố việc đổi."
            )
    run_id = new_id()
    root = output / run_id
    root.mkdir(parents=True, exist_ok=False)
    results: list[EvaluationResult] = []
    for case in dataset.cases:
        if split not in {"all", case.split}:
            continue
        folder = root / case.case_id
        folder.mkdir()
        request = case.input.research_request()
        if dataset.is_synthetic:
            sources = load_fixtures(Path("data/fixtures"), case.input.source_ids)
        else:
            sources = [
                fetch_public(url, f"U{i}", settings) for i, url in enumerate(case.input.urls, 1)
            ]
        spans, coverage = retrieve(request, sources, settings.max_context_chars)
        hashes = {source.source_id: source.content_hash for source in sources}
        # Freeze expectation separately before CLI execution. No evaluator data goes to CLI.
        expected = load_expected(case, cases)
        (folder / "expected_evaluator_only.json").write_text(
            json.dumps(expected, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        request_path, sources_path = folder / "request.json", folder / "sources.json"
        request_path.write_text(request.model_dump_json(indent=2), encoding="utf-8")
        sources_path.write_bytes(sources_adapter.dump_json(sources, indent=2))
        (folder / "retrieval.json").write_text(
            json.dumps(
                {
                    "coverage": coverage.model_dump(),
                    "selected_span_ids": [span.span_id for span in spans],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        report_path = folder / "report.json"
        command = [
            sys.executable,
            "-m",
            "gamota_research.cli",
            "run",
            "--request",
            str(request_path),
            "--sources",
            str(sources_path),
            "--out",
            str(report_path),
        ]
        result = run_cli(
            command, settings.max_llm_requests_per_run * (settings.llm_timeout_seconds + 5) + 30
        )
        (folder / "cli.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        checks: dict[str, JsonValue] = {
            "cli_exit_code": result.returncode,
            "live_ready": settings.live_ready,
            "max_context_chars": settings.max_context_chars,
            "source_hashes": hashes,
            "coverage": coverage.model_dump(mode="json"),
            "request_count": 0 if not settings.live_ready else None,
        }
        failure_path = report_path.with_suffix(".failure.json")
        if failure_path.exists():
            failure = FailureRecord.model_validate_json(failure_path.read_bytes())
            checks["request_count"] = failure.usage.request_count
            checks["failure_diagnostics"] = failure.model_dump(mode="json")
        if report_path.exists() and result.returncode == 0:
            bundle = load_bundle(report_path.read_bytes())
            checks.update(automatic_checks(bundle))
            checks["request_count"] = bundle.report.usage.request_count
            actual = "CLI tạo report thật; locator/hash/IDs hợp lệ. Chưa chấm semantic support/completeness."
            verdict = "BLOCKED"
            learned = "Cần người đọc nguồn chấm mọi material fact và phản chứng trước khi gọi PASS."
        else:
            actual = (result.stdout + result.stderr).strip()
            verdict = failure_verdict(actual, live_ready=settings.live_ready)
            learned = (
                "Thiếu cấu hình live; không thể đánh giá khả năng sinh kết quả của model."
                if not settings.live_ready
                else "Đọc cli.log để phân biệt lỗi model, dữ liệu và hạ tầng; chưa chấm ngữ nghĩa."
            )
        item = EvaluationResult(
            run_id=run_id,
            case_id=case.case_id,
            split=case.split,
            input_hashes=hashes,
            code_revision=revision,
            model_id=settings.llm_model or None,
            actual_output_path=str(report_path) if report_path.exists() else None,
            expected=expected,
            actual=actual,
            verdict=verdict,
            learned=learned,
            checks=checks,
        )
        (folder / "result.json").write_text(item.model_dump_json(indent=2), encoding="utf-8")
        results.append(item)
        typer.echo(f"{case.case_id}: {verdict}; cli_exit={result.returncode}")
    (root / "results.json").write_bytes(
        TypeAdapter(list[EvaluationResult]).dump_json(results, indent=2)
    )
    typer.echo(f"Artifacts: {root}")


if __name__ == "__main__":
    app()
