from pathlib import Path

from typer.testing import CliRunner

from gamota_research.cli import app


def test_cli_fixture_inspection_without_key(tmp_path: Path) -> None:
    # Given: the documented CLI, no LLM needed.
    runner = CliRunner()
    sources = tmp_path / "sources.json"
    result = runner.invoke(app, ["fixtures", "--out", str(sources)])
    assert result.exit_code == 0, result.output
    # When: running the production retrieval command on those snapshots.
    result = runner.invoke(
        app,
        [
            "inspect",
            "--request",
            "examples/request.json",
            "--sources",
            str(sources),
            "--out",
            str(tmp_path / "selected.json"),
        ],
    )
    # Then: source spans are real, with no claim generator fallback.
    assert result.exit_code == 0, result.output
    assert '"claims_generated": false' in (tmp_path / "selected.json").read_text(encoding="utf-8")
