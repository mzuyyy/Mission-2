"""Real browser QA, run separately: uv run pytest tests/browser -m browser -q."""

import json
from pathlib import Path

import httpx
import pytest
from playwright.sync_api import expect, sync_playwright

from gamota_research.ingestion.normalize import document
from gamota_research.llm import ChatGenerator
from gamota_research.pipeline import run_research
from tests.integration.test_pipeline import WireFixture, configured, request


@pytest.mark.browser
def test_browser_offline_replay_review_and_responsive(tmp_path: Path, server_url: str) -> None:
    # Given: a real server and an explicitly synthetic, wire-mocked report for replay QA.
    artifacts = Path("eval/runs/browser")
    artifacts.mkdir(parents=True, exist_ok=True)
    source = document("S1", "Nguồn giả lập", "Doanh thu chưa rõ phương pháp đo.").model_copy(
        update={"is_synthetic": True, "original_url": "https://example.com/report"}
    )
    bundle = run_research(
        request(),
        [source],
        ChatGenerator(configured(), httpx.MockTransport(WireFixture())),
        configured(),
    )
    bundle_path = tmp_path / "synthetic_replay.json"
    bundle_path.write_text(bundle.model_dump_json(), encoding="utf-8")
    errors: list[str] = []
    screenshots: list[str] = []
    # When: driving the actual Streamlit UI in full Chromium, without a live LLM.
    with (
        sync_playwright() as playwright,
        playwright.chromium.launch(channel="chromium", headless=True) as browser,
    ):
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(server_url, wait_until="domcontentloaded")
        expect(
            page.get_by_role("heading", name="Nghiên cứu thị trường game", exact=True)
        ).to_be_visible()
        expect(
            page.get_by_role("button", name="Sinh nhận định từ nguồn", exact=True)
        ).to_be_disabled()
        page.get_by_text("Kiểm tra offline bằng nguồn giả lập", exact=True).click()
        page.get_by_role("button", name="Nạp nguồn giả lập", exact=True).click()
        page.get_by_role("tab", name="Nguồn", exact=True).click()
        expect(page.get_by_text("S01 · ok", exact=True)).to_be_visible()
        page.get_by_text("S01 · ok", exact=True).click()
        expect(page.get_by_text("DỮ LIỆU GIẢ LẬP", exact=True).first).to_be_visible()
        page.screenshot(path=str(artifacts / "fixture_source.png"), full_page=True)

        # A public-input error remains visible in coverage, without touching private services.
        page.get_by_role("textbox", name="URL công khai, mỗi dòng một URL").fill(
            "http://127.0.0.1/private"
        )
        page.get_by_role("button", name="Đọc URL/PDF", exact=True).click()
        expect(page.get_by_text("U1 · failed", exact=True)).to_be_attached()
        page.get_by_role("tab", name="Nguồn", exact=True).click()
        expect(page.get_by_text("U1 · failed", exact=True)).to_be_visible()

        expect(
            page.get_by_role("heading", name="Mở kết quả đã lưu (replay)", exact=True)
        ).to_be_visible()
        page.locator('input[type="file"]').nth(1).set_input_files(str(bundle_path.resolve()))
        page.screenshot(path=str(artifacts / "upload_state.png"), full_page=True)
        (artifacts / "upload_state.txt").write_text(
            page.locator("body").inner_text(), encoding="utf-8"
        )
        try:
            page.get_by_role("button", name="Mở replay", exact=True).click(timeout=10000)
        finally:
            page.screenshot(path=str(artifacts / "after_upload.png"), full_page=True)
            (artifacts / "after_upload.txt").write_text(
                page.locator("body").inner_text(), encoding="utf-8"
            )
        expect(page.get_by_text("REPLAY · kết quả đã lưu lúc", exact=False)).to_be_visible()
        page.get_by_role("tab", name="Kết quả", exact=True).click()
        page.get_by_text("Mở bằng chứng C1", exact=True).click()
        quote_code = (
            page.get_by_role("tabpanel", name="Kết quả", exact=True)
            .locator("code")
            .filter(has_text=source.normalized_text)
        )
        expect(quote_code).to_be_visible()
        expect(page.get_by_text(source.normalized_text, exact=True).first).to_be_visible()
        expect(
            page.get_by_text(
                f"E1 · S1 · trang N/A · ký tự [0, {len(source.normalized_text)})", exact=True
            ).first
        ).to_be_visible()
        page.get_by_role("tab", name="Kiểm tra", exact=True).click()
        page.get_by_role("textbox", name="Ghi chú đánh giá", exact=True).fill(
            "Cần đọc phương pháp gốc; browser QA synthetic."
        )
        page.get_by_role("button", name="Lưu đánh giá thành phiên bản mới", exact=True).click()
        expect(page.get_by_text("version 2", exact=False).first).to_be_visible()
        with page.expect_download() as download:
            page.get_by_role("button", name="Xuất JSON và snapshot nguồn", exact=True).click()
        downloaded = artifacts / "reviewed_synthetic.json"
        download.value.save_as(str(downloaded))
        actual = json.loads(downloaded.read_text(encoding="utf-8"))
        assert actual["report"]["version"] == 2
        assert actual["report"]["review_history"][0]["decision"] == "needs_review"
        page.get_by_role("tab", name="Kết quả", exact=True).click()
        if not quote_code.is_visible():
            page.get_by_text("Mở bằng chứng C1", exact=True).click()
        expect(quote_code).to_be_visible()
        for width in (375, 768, 1280):
            page.set_viewport_size({"width": width, "height": 900})
            page.get_by_text(
                f"E1 · S1 · trang N/A · ký tự [0, {len(source.normalized_text)})", exact=True
            ).first.scroll_into_view_if_needed()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            assert page.locator('[data-testid="stMain"]').evaluate(
                "el => el.scrollWidth <= el.clientWidth"
            )
            target = artifacts / f"replay_{width}.png"
            expect(quote_code).to_be_visible()
            page.screenshot(path=str(target), full_page=True, animations="disabled")
            screenshots.append(str(target))
        assert errors == []
    (artifacts / "result.json").write_text(
        json.dumps(
            {
                "mode": "synthetic_replay_browser_qa",
                "live_llm": False,
                "screenshots": screenshots,
                "page_errors": errors,
                "checks": [
                    "disabled_without_key",
                    "fixture_inspection",
                    "private_url_error",
                    "replay_quote",
                    "review_version",
                    "json_download",
                    "375_768_1280_no_overflow",
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
