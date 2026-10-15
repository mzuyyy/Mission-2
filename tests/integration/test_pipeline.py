import json
from pathlib import Path

import httpx
import pytest
from pydantic import SecretStr

from gamota_research.config import Settings
from gamota_research.contracts import Claim, EvidenceLink, Recommendation, ResearchRequest
from gamota_research.errors import ResearchError
from gamota_research.export import export_markdown
from gamota_research.ingestion.normalize import document
from gamota_research.llm import ChatGenerator
from gamota_research.models import Extraction, Synthesis
from gamota_research.pipeline import run_research
from gamota_research.storage import Workspace, load_bundle, review


def configured() -> Settings:
    return Settings(
        _env_file=None,
        llm_api_base="https://llm.example/v1",
        llm_api_key=SecretStr("test-only-not-a-real-key"),
        llm_model="mock-wire",
    )


def request(question: str = "Nguồn nói gì về chỉ số hiện tại?") -> ResearchRequest:
    return ResearchRequest(
        question=question,
        country=["VN"],
        platforms=["Android"],
        decision_goal="verify_claim",
        clarified=True,
    )


def response(content: str) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "choices": [{"message": {"content": content}, "finish_reason": "stop"}],
            "usage": {"total_tokens": 10},
        },
    )


class WireFixture:
    """Mutable test-only wire adapter; echoes provided input, never used by the application."""

    def __init__(self) -> None:
        self.payloads: list[str] = []

    def __call__(self, req: httpx.Request) -> httpx.Response:
        body = json.loads(req.content)
        payload = json.loads(body["messages"][1]["content"])
        self.payloads.append(body["messages"][1]["content"])
        if "untrusted_spans" in payload:
            span = payload["untrusted_spans"][0]
            extracted = {
                "evidence": [
                    {
                        "evidence_id": "E1",
                        "source_id": span["source_id"],
                        "span_id": span["span_id"],
                        "quote": span["text"],
                    }
                ],
                "missing_data": ["Chưa có phương pháp đo."],
            }
            return response(json.dumps(extracted, ensure_ascii=False))
        evidence = payload["evidence"][0]
        synthesis = Synthesis(
            claims=[
                Claim(
                    claim_id="C1",
                    text=evidence["quote"],
                    kind="fact",
                    assessment="supported",
                    evidence_links=[EvidenceLink(evidence_id="E1", relation="supports")],
                )
            ],
            conflicts=[],
            recommendations=[
                Recommendation(
                    recommendation_id="R1",
                    action="Khảo sát thêm",
                    rationale="Chưa đủ dữ liệu",
                    premise_claim_ids=["C1"],
                    next_step="Xin mô tả phương pháp đo",
                )
            ],
            missing_data=["Chưa có kiểm chứng độc lập."],
        )
        return response(synthesis.model_dump_json())


def test_two_questions_share_pipeline_and_retain_source_quotes(tmp_path: Path) -> None:
    # Given: two different questions and synthetic source snapshots; only LLM wire is mocked.
    wire = WireFixture()
    generator = ChatGenerator(configured(), httpx.MockTransport(wire))
    source = document("S1", "Synthetic", "Tín hiệu nhu cầu của nhóm X tăng.").model_copy(
        update={"is_synthetic": True}
    )
    # When: the real pipeline, storage, replay and export are exercised.
    bundle = run_research(request(), [source], generator, configured())
    workspace = Workspace(tmp_path)
    initial = workspace.save(bundle)
    updated = review(bundle, "C1", "reject", "Cần thêm phương pháp đo")
    reviewed = workspace.save(updated)
    replay = load_bundle(reviewed.read_bytes())
    # Then: citations survive review/export and original snapshot remains unchanged.
    assert bundle.report.evidence[0].quote == source.normalized_text
    assert bundle.report.mode == "fixture"
    assert bundle.report.is_synthetic
    assert initial.read_bytes() != reviewed.read_bytes()
    assert replay.report.mode == "replay"
    assert replay.report.claims[0].human_review == "reject"
    assert replay.report.review_history[0].previous_claim is not None
    assert "DỮ LIỆU GIẢ LẬP" in export_markdown(replay)
    assert "E1" in export_markdown(replay)
    assert generator.usage().request_count == 2
    assert all("expected" not in p and "case_id" not in p for p in wire.payloads)


def test_different_task_uses_new_source_and_no_question_keyword_branch() -> None:
    # Given: unrelated question/source text, still using the exact same mock wire protocol.
    generator = ChatGenerator(configured(), httpx.MockTransport(WireFixture()))
    source = document(
        "TH1", "Synthetic competition", "Danh mục tại Thái Lan có đối thủ Y."
    ).model_copy(update={"is_synthetic": True})
    # When.
    bundle = run_research(
        request("Đối thủ nào có trong danh mục Thái Lan?"), [source], generator, configured()
    )
    # Then: no answer belonging to the first task leaks into this task.
    assert bundle.report.evidence[0].quote == source.normalized_text
    assert bundle.report.claims[0].text == source.normalized_text


def test_single_incomplete_output_is_retried_once() -> None:
    # Given: provider truncates once (finish length), then returns a valid extraction.
    replies = iter(
        [
            httpx.Response(
                200,
                json={
                    "choices": [
                        {"message": {"content": '{"evidence": []'}, "finish_reason": "length"}
                    ],
                    "usage": {"total_tokens": 10},
                },
            ),
            response(json.dumps({"evidence": [], "missing_data": []})),
        ]
    )
    generator = ChatGenerator(configured(), httpx.MockTransport(lambda _req: next(replies)))
    # When / Then: one immediate retry, no sample fallback.
    assert generator.generate(Extraction, "JSON", "{}").evidence == []
    assert generator.usage().request_count == 2


def test_persistent_incomplete_output_aborts_without_sample_report() -> None:
    # Given: provider truncates on every attempt.
    truncated = httpx.Response(
        200,
        json={
            "choices": [{"message": {"content": '{"evidence": []'}, "finish_reason": "length"}],
            "usage": {"total_tokens": 10},
        },
    )
    generator = ChatGenerator(configured(), httpx.MockTransport(lambda _req: truncated))
    # When / Then.
    with pytest.raises(ResearchError, match="provider_incomplete"):
        generator.generate(Extraction, "JSON", "{}")
    assert generator.usage().request_count == 2


def test_invalid_synthesis_is_retried_once_and_report_survives() -> None:
    # Given: first synthesis draft has an inference without reasoning (observed live
    # failure mode), second draft is complete.
    calls = {"synthesis": 0}
    quote = "Tín hiệu nhu cầu của nhóm X tăng 15%."

    def handler(req: httpx.Request) -> httpx.Response:
        payload = json.loads(json.loads(req.content)["messages"][1]["content"])
        if "untrusted_spans" in payload:
            span = payload["untrusted_spans"][0]
            return response(
                json.dumps(
                    {
                        "evidence": [
                            {
                                "evidence_id": "E1",
                                "source_id": span["source_id"],
                                "span_id": span["span_id"],
                                "quote": quote,
                            }
                        ],
                        "missing_data": [],
                    },
                    ensure_ascii=False,
                )
            )
        calls["synthesis"] += 1
        draft = {
            "claims": [
                {
                    "claim_id": "C0",
                    "text": quote,
                    "kind": "fact",
                    "material": True,
                    "assessment": "supported",
                    "evidence_links": [{"evidence_id": "E1", "relation": "supports"}],
                    "premise_claim_ids": [],
                    "assumptions": [],
                    "reasoning": None,
                    "missing_data": [],
                    "limitations": [],
                    "human_review": "unreviewed",
                },
                {
                    "claim_id": "C1",
                    "text": "Không thể kết luận nhu cầu tăng.",
                    "kind": "inference",
                    "material": True,
                    "assessment": "insufficient",
                    "evidence_links": [],
                    "premise_claim_ids": ["C0"],
                    "assumptions": ["Thiếu dữ liệu game riêng"],
                    "reasoning": "Từ thiếu dữ liệu nên không kết luận."
                    if calls["synthesis"] > 1
                    else None,
                    "missing_data": [],
                    "limitations": [],
                    "human_review": "unreviewed",
                },
            ],
            "conflicts": [],
            "recommendations": [
                {
                    "recommendation_id": "R1",
                    "action": "Thu thập thêm dữ liệu",
                    "rationale": "Chưa đủ dữ liệu",
                    "premise_claim_ids": ["C1"],
                    "blocking_unknowns": [],
                    "blocked": True,
                    "next_step": "Xin báo cáo chi tiết",
                }
            ],
            "missing_data": [],
        }
        return response(json.dumps(draft, ensure_ascii=False))

    generator = ChatGenerator(configured(), httpx.MockTransport(handler))
    # When.
    bundle = run_research(
        request(),
        [document("S1", "Synthetic", quote)],
        generator,
        configured(),
    )
    # Then: the valid second draft becomes the report, retry visible in warnings/usage.
    assert bundle.report.claims[1].reasoning is not None
    assert calls["synthesis"] == 2
    assert generator.usage().request_count == 3
    assert any("tổng hợp" in warning for warning in bundle.report.coverage.warnings)


def test_persistent_invalid_synthesis_aborts_without_sample_report() -> None:
    # Given: every synthesis draft references a nonexistent evidence ID.
    def handler(req: httpx.Request) -> httpx.Response:
        payload = json.loads(json.loads(req.content)["messages"][1]["content"])
        if "untrusted_spans" in payload:
            span = payload["untrusted_spans"][0]
            return response(
                json.dumps(
                    {
                        "evidence": [
                            {
                                "evidence_id": "E1",
                                "source_id": span["source_id"],
                                "span_id": span["span_id"],
                                "quote": span["text"],
                            }
                        ],
                        "missing_data": [],
                    }
                )
            )
        return response(
            json.dumps(
                {
                    "claims": [
                        {
                            "claim_id": "C1",
                            "text": "Nhu cầu tăng.",
                            "kind": "fact",
                            "material": True,
                            "assessment": "supported",
                            "evidence_links": [{"evidence_id": "MISSING", "relation": "supports"}],
                            "premise_claim_ids": [],
                            "assumptions": [],
                            "reasoning": None,
                            "missing_data": [],
                            "limitations": [],
                            "human_review": "unreviewed",
                        }
                    ],
                    "conflicts": [],
                    "recommendations": [],
                    "missing_data": [],
                }
            )
        )

    generator = ChatGenerator(configured(), httpx.MockTransport(handler))
    # When / Then: one bounded retry, then abort; no report fallback.
    with pytest.raises(ResearchError, match="dangling_id"):
        run_research(
            request(), [document("S1", "Test", "Revenue unknown")], generator, configured()
        )
    assert generator.usage().request_count == 3


def test_nonexistent_quote_aborts_before_synthesis() -> None:
    # Given: model invents a quote on every extraction attempt.
    def handler(req: httpx.Request) -> httpx.Response:
        payload = json.loads(json.loads(req.content)["messages"][1]["content"])
        span = payload["untrusted_spans"][0]
        return response(
            json.dumps(
                {
                    "evidence": [
                        {
                            "evidence_id": "E1",
                            "source_id": span["source_id"],
                            "span_id": span["span_id"],
                            "quote": "invented profit",
                        }
                    ]
                }
            )
        )

    generator = ChatGenerator(configured(), httpx.MockTransport(handler))
    # When / Then: one bounded citation retry, then abort; no report fallback.
    with pytest.raises(ResearchError, match="quote"):
        run_research(
            request(), [document("S1", "Test", "Revenue unknown")], generator, configured()
        )
    assert generator.usage().request_count == 2


def test_paraphrased_quote_is_retried_once_and_report_survives() -> None:
    # Given: first extraction paraphrases the quote (observed live failure mode), second is exact.
    calls = {"extraction": 0}

    def handler(req: httpx.Request) -> httpx.Response:
        payload = json.loads(json.loads(req.content)["messages"][1]["content"])
        if "untrusted_spans" not in payload:
            evidence = payload["evidence"][0]
            synthesis = Synthesis(
                claims=[
                    Claim(
                        claim_id="C1",
                        text=evidence["quote"],
                        kind="fact",
                        assessment="supported",
                        evidence_links=[EvidenceLink(evidence_id="E1", relation="supports")],
                    )
                ],
                conflicts=[],
                recommendations=[
                    Recommendation(
                        recommendation_id="R1",
                        action="Khảo sát thêm",
                        rationale="Chưa đủ dữ liệu",
                        premise_claim_ids=["C1"],
                        next_step="Xin mô tả phương pháp đo",
                    )
                ],
                missing_data=[],
            )
            return response(synthesis.model_dump_json())
        calls["extraction"] += 1
        span = payload["untrusted_spans"][0]
        quote = (
            "tín hiệu nhu cầu của nhóm X tăng"
            if calls["extraction"] == 1  # paraphrase: not a substring of the source
            else span["text"]
        )
        return response(
            json.dumps(
                {
                    "evidence": [
                        {
                            "evidence_id": "E1",
                            "source_id": span["source_id"],
                            "span_id": span["span_id"],
                            "quote": quote,
                        }
                    ],
                    "missing_data": ["Chưa có phương pháp đo."],
                },
                ensure_ascii=False,
            )
        )

    generator = ChatGenerator(configured(), httpx.MockTransport(handler))
    # When.
    bundle = run_research(
        request(),
        [document("S1", "Synthetic", "Tín hiệu nhu cầu của nhóm X tăng 15%.")],
        generator,
        configured(),
    )
    # Then: only the verified quote enters the report, and the retry is visible in usage.
    assert bundle.report.evidence[0].quote == "Tín hiệu nhu cầu của nhóm X tăng 15%."
    assert calls["extraction"] == 2
    assert generator.usage().request_count == 3
    assert any("quote" in warning for warning in bundle.report.coverage.warnings)


def test_invalid_json_repair_is_bounded() -> None:
    # Given: malformed provider output on every request.
    generator = ChatGenerator(configured(), httpx.MockTransport(lambda _req: response("bad JSON")))
    # When / Then: one repair only, no report fallback.
    with pytest.raises(ResearchError, match="provider_json"):
        generator.generate(Extraction, "JSON", "{}")
    assert generator.usage().request_count == 2


def test_retry_and_second_stage_share_total_budget() -> None:
    # Given: first stage consumes both allowed requests through one JSON repair.
    settings = configured().model_copy(update={"max_llm_requests_per_run": 2})
    replies = iter([response("bad JSON"), response('{"evidence": []}')])
    generator = ChatGenerator(settings, httpx.MockTransport(lambda _req: next(replies)))
    generator.generate(Extraction, "JSON", "{}")
    # When / Then: no budget is reset at stage boundary.
    with pytest.raises(ResearchError, match="request_budget"):
        generator.generate(Synthesis, "JSON", "{}")
    assert generator.usage().request_count == 2


def test_missing_key_never_calls_provider() -> None:
    # Given / When / Then.
    with pytest.raises(ResearchError, match="llm_not_configured"):
        ChatGenerator(
            Settings(_env_file=None, llm_api_base="", llm_model="", llm_api_key=SecretStr(""))
        )


def test_tampered_replay_source_is_rejected() -> None:
    # Given: an otherwise valid saved bundle.
    bundle = run_research(
        request(),
        [document("S1", "Test", "Revenue unknown")],
        ChatGenerator(configured(), httpx.MockTransport(WireFixture())),
        configured(),
    )
    modified = bundle.sources[0].model_copy(update={"normalized_text": "tampered"})
    data = bundle.model_copy(update={"sources": [modified]}).model_dump_json().encode()
    # When / Then.
    with pytest.raises(ResearchError, match="replay_hash"):
        load_bundle(data)
