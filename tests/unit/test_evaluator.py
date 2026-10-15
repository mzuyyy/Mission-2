import pytest


@pytest.mark.parametrize(
    ("ready", "actual", "expected"),
    [
        (False, "llm_not_configured: missing", "BLOCKED"),
        (True, "provider_network: timeout", "BLOCKED"),
        (True, "provider_http: Provider trả HTTP 401", "BLOCKED"),
        (True, "evaluation_timeout: process deadline", "BLOCKED"),
        (True, "provider_json: schema invalid", "FAIL"),
        (True, "citation: quote không khớp", "FAIL"),
    ],
)
def test_evaluator_does_not_count_infrastructure_blocker_as_product_failure(
    *, ready: bool, actual: str, expected: str
) -> None:
    from eval.evaluation_support import failure_verdict

    # Given / When / Then: network/configuration cannot establish a model quality failure.
    assert failure_verdict(actual, live_ready=ready) == expected


def test_cli_deadline_becomes_recordable_blocker(monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess

    from eval.evaluation_support import run_cli

    # Given: an actual process timeout shape, injected at the process boundary.
    def timeout(*_args: str, **_kwargs: str) -> None:
        raise subprocess.TimeoutExpired("python", 1)

    monkeypatch.setattr(subprocess, "run", timeout)
    # When / Then: the evaluator can write its result instead of dropping the run.
    result = run_cli(["python", "-m", "gamota_research.cli"], 1)
    assert result.returncode == 124
    assert result.stderr.startswith("evaluation_timeout:")
