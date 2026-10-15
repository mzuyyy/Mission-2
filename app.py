"""Run with: uv run streamlit run app.py."""

import streamlit as st
from pydantic import ValidationError

from gamota_research.config import Settings
from gamota_research.errors import ResearchError
from gamota_research.llm import ChatGenerator
from gamota_research.pipeline import run_research
from gamota_research.ui_input import request_form
from gamota_research.ui_report import report_tabs
from gamota_research.ui_state import current_session


def main() -> None:
    st.set_page_config(page_title="Gamota · Nghiên cứu có căn cứ", layout="centered")
    st.title("Nghiên cứu thị trường game")
    st.caption("Câu hỏi → nguồn → bằng chứng → nhận định → bạn kiểm chứng")
    try:
        settings = Settings()
        session = current_session()
        if not settings.live_ready:
            st.warning(
                "Live LLM bị chặn: chưa cấu hình API base/model/key. Điền .env tại máy; không dán key vào chat. Đọc nguồn và replay vẫn dùng được."
            )
        else:
            st.info(
                "Sinh live sẽ gửi nguồn tới một dịch vụ LLM đã cấu hình. Không có tự động đổi provider."
            )
        request, consent = request_form(session, settings)
        ready = bool(
            settings.live_ready
            and request
            and request.clarified
            and consent
            and any(s.normalized_text for s in session.sources)
        )
        if st.button("Sinh nhận định từ nguồn", disabled=not ready, type="primary") and request:
            # Clear an older report before a new attempt so provider failure cannot show stale success.
            session.bundle = None
            session.request = request
            with st.spinner(
                "Đang trích evidence và tổng hợp; chưa phải kết quả đã được chuyên viên xác minh…"
            ):
                generator = ChatGenerator(settings)
                bundle = run_research(request, session.sources, generator, settings)
                session.workspace.save(bundle)
                session.bundle = bundle
        report_tabs(session)
        st.caption(
            "Dữ liệu trong phiên được lưu local ở runs/; không dùng cache global. Export trước khi đóng phiên/host ephemeral."
        )
    except ResearchError as error:
        st.error(str(error))
        st.info("Không tạo báo cáo mẫu. Kiểm tra nguồn/cấu hình và thử lại trong ngân sách đã đặt.")
    except (ValidationError, OSError):
        st.error("Cấu hình, dữ liệu hoặc quyền ghi chưa hợp lệ; kiểm tra schema và thư mục runs/.")


if __name__ == "__main__":
    main()
