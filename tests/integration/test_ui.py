from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_ui_without_key_reads_fixtures_without_generating_claims() -> None:
    # Given: a fresh Streamlit session.
    app = AppTest.from_file(Path("app.py").resolve(), default_timeout=20).run()
    assert not app.exception
    # When: loading source fixtures through the actual app button.
    next(button for button in app.button if button.label == "Nạp nguồn giả lập").click().run()
    # Then: source text is inspectable, no generated claims or live success is shown.
    assert not app.exception
    assert any("DỮ LIỆU GIẢ LẬP" in warning.value for warning in app.warning)
    assert any(
        button.disabled for button in app.button if button.label == "Sinh nhận định từ nguồn"
    )
    assert len(app.tabs) == 4
