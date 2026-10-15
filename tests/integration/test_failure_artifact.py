import json
from pathlib import Path

import httpx
import pytest
from typer.testing import CliRunner

from gamota_research.cli import app
from gamota_research.llm import ChatGenerator
from tests.integration.test_pipeline import configured


def test_live_cli_failure_keeps_usage_and_safe_diagnostics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    generator = ChatGenerator(
        configured(),
        httpx.MockTransport(
            lambda _req: httpx.Response(
                429, json={"error": {"message": "free-models-per-day private body"}}
            )
        ),
    )
    monkeypatch.setattr("gamota_research.cli.ChatGenerator", lambda _settings: generator)
    runner = CliRunner()
    sources = tmp_path / "sources.json"
    assert runner.invoke(app, ["fixtures", "--out", str(sources)]).exit_code == 0
    report = tmp_path / "report.json"
    result = runner.invoke(
        app,
        [
            "run",
            "--request",
            "examples/request.json",
            "--sources",
            str(sources),
            "--out",
            str(report),
        ],
    )
    assert result.exit_code == 2
    assert not report.exists()
    failure = json.loads(report.with_suffix(".failure.json").read_text(encoding="utf-8"))
    assert failure["usage"]["request_count"] == 1
    assert failure["provider_failure"]["category"] == "daily_quota"
    assert failure["model_id"] == "mock-wire"
    assert "private body" not in json.dumps(failure)
    assert "test-only-not-a-real-key" not in json.dumps(failure)
