import json
from datetime import date
from pathlib import Path
from typing import Literal

import streamlit as st
from pydantic import TypeAdapter, ValidationError

from gamota_research.config import Settings
from gamota_research.contracts import Contract, ResearchRequest, SourceDocument
from gamota_research.errors import ResearchError
from gamota_research.fixtures import load_fixtures
from gamota_research.ingestion.pdf import parse_pdf
from gamota_research.ingestion.public_url import fetch_public
from gamota_research.storage import load_bundle
from gamota_research.ui_state import Session


class SourceMetadata(Contract):
    source_id: str
    publisher: str | None = None
    country: list[str] | None = None
    platforms: list[str] | None = None
    data_period: str | None = None
    methodology: str | None = None
    conflicts_of_interest: str | None = None
    original_root_id: str | None = None
    root_relation_reason: str | None = None
    source_kind: (
        Literal["original_report", "company_disclosure", "syndication", "opinion", "unknown"] | None
    ) = None
    published_at: date | None = None
    period_start: date | None = None
    period_end: date | None = None


def apply_metadata(sources: list[SourceDocument], raw: str) -> list[SourceDocument]:
    if not raw.strip():
        return sources
    metadata = TypeAdapter(list[SourceMetadata]).validate_json(raw)
    known_ids = {s.source_id for s in sources}
    if any(item.source_id not in known_ids for item in metadata):
        raise ResearchError("metadata_id", "Metadata có source_id chưa được nhập.")
    mapped = {item.source_id: item for item in metadata}
    result: list[SourceDocument] = []
    for original in sources:
        source = original
        if source.source_id in mapped:
            values = mapped[source.source_id].model_dump(exclude={"source_id"}, exclude_unset=True)
            source = SourceDocument.model_validate(
                {
                    **source.model_dump(),
                    **values,
                    "metadata_provenance": {
                        **source.metadata_provenance,
                        **dict.fromkeys(values, "user"),
                    },
                }
            )
        result.append(source)
    return result


PLATFORM_OPTIONS: tuple[str, ...] = (
    "Android",
    "iOS",
    "PC",
    "Web",
    "Console",
    "PlayStation",
    "Xbox",
    "Nintendo Switch",
)


def request_form(session: Session, settings: Settings) -> tuple[ResearchRequest | None, bool]:
    st.subheader("Câu hỏi và phạm vi")
    question = st.text_area(
        "Câu hỏi nghiên cứu",
        placeholder="Bạn muốn kiểm tra nhận định hay khảo sát cơ hội nào?",
        key="question",
    )
    country = st.text_input("Một quốc gia/thị trường", value="VN")
    platforms = st.multiselect(
        "Nền tảng (bấm để mở bảng chọn, tích vào các ô)",
        options=list(PLATFORM_OPTIONS),
        default=["Android"],
        key="platforms",
    )
    extra_platforms = st.text_input(
        "Nền tảng khác (tự nhập, phân cách bằng dấu phẩy)",
        key="extra_platforms",
    )
    start_unknown = st.checkbox("Chưa biết từ ngày", value=True, key="start_unknown")
    period_start = st.date_input(
        "Từ ngày (bấm để mở bảng chọn ngày)",
        value=None,
        disabled=start_unknown,
        key="period_start",
    )
    end_unknown = st.checkbox("Chưa biết đến ngày", value=True, key="end_unknown")
    period_end = st.date_input(
        "Đến ngày (bấm để mở bảng chọn ngày)",
        value=None,
        disabled=end_unknown,
        key="period_end",
    )
    goal = st.selectbox(
        "Tiêu chí quyết định",
        [
            "Nhu cầu người chơi",
            "Khả năng kiếm tiền",
            "Cạnh tranh/phát hành",
            "Kiểm tra một nhận định",
            "So sánh cơ hội theo tiêu chí bên dưới",
        ],
    )
    constraints = st.text_area(
        "Tiêu chí cụ thể và ràng buộc", help="Ví dụ: chỉ so sánh lượt tải, chưa suy ra lợi nhuận."
    )
    alternatives = st.text_input("Các phương án nếu cần so sánh (phân cách bằng dấu phẩy)")
    clarified = st.checkbox("Tôi đã chốt tiêu chí và chấp nhận các trường phạm vi còn unknown")
    if not clarified:
        st.info(
            "Bạn muốn đánh giá theo nhu cầu, khả năng kiếm tiền hay cạnh tranh? Chọn tiêu chí phía trên rồi xác nhận phạm vi."
        )
    consent = st.checkbox(
        "Tôi có quyền gửi các nguồn đã chọn tới dịch vụ LLM được cấu hình",
        help="Chỉ gửi khi bấm Sinh nhận định. Demo public chỉ dùng nguồn công khai.",
    )
    request = None
    if question.strip():
        try:
            request = ResearchRequest(
                question=question,
                country=[country.strip()],
                platforms=[
                    *platforms,
                    *(p.strip() for p in extra_platforms.split(",") if p.strip()),
                ],
                period_start=None if start_unknown else period_start,
                period_end=None if end_unknown else period_end,
                decision_goal=goal,
                alternatives=[p.strip() for p in alternatives.split(",") if p.strip()],
                constraints=[constraints] if constraints else [],
                clarified=clarified,
            )
        except (ValueError, ValidationError):
            st.error("Kiểm tra câu hỏi, thị trường, nền tảng và khoảng ngày (từ ngày ≤ đến ngày).")
    source_input(session, settings)
    return request, consent


def source_input(session: Session, settings: Settings) -> None:
    st.subheader("Nguồn do bạn cung cấp")
    with st.form("sources"):
        urls = st.text_area(
            "URL công khai, mỗi dòng một URL",
            help="HTML/text UTF-8 hoặc PDF có lớp chữ. Không chạy JavaScript.",
        )
        pdfs = st.file_uploader(
            "PDF có lớp chữ",
            type=["pdf"],
            accept_multiple_files=True,
            max_upload_size=settings.max_file_mb,
            key="source_pdf_uploads",
        )
        metadata = st.text_area(
            "Metadata nguồn (JSON tùy chọn)",
            placeholder='[{"source_id":"U1","country":["VN"],"data_period":"2025-Q3"}]',
        )
        submitted = st.form_submit_button("Đọc URL/PDF")
    if submitted:
        lines = [line.strip() for line in urls.splitlines() if line.strip()]
        if len(lines) + len(pdfs) > settings.max_sources:
            st.error(f"Tối đa {settings.max_sources} nguồn mỗi lượt.")
        else:
            with st.spinner("Đang đọc nguồn, giữ snapshot và vị trí đoạn trích…"):
                sources = [fetch_public(url, f"U{i}", settings) for i, url in enumerate(lines, 1)]
                for i, upload in enumerate(pdfs, 1):
                    sources.append(parse_pdf(upload.getvalue(), f"P{i}", upload.name, settings))
                try:
                    session.sources = apply_metadata(sources, metadata)
                    session.bundle = None
                    st.success(f"Đã xử lý {len(sources)} nguồn. Xem trạng thái đọc ở tab Nguồn.")
                except (ResearchError, ValidationError, json.JSONDecodeError):
                    st.error(
                        "Metadata JSON không hợp lệ; cần danh sách đúng schema và source_id U1/P1…"
                    )
    with st.expander("Kiểm tra offline bằng nguồn giả lập"):
        st.warning(
            "DỮ LIỆU GIẢ LẬP. Nạp nguồn không tạo nhận định và không chứng minh chất lượng LLM."
        )
        if st.button("Nạp nguồn giả lập"):
            session.sources = load_fixtures(
                Path("data/fixtures"), max_chars=settings.max_source_chars
            )
            session.bundle = None
    with st.container(border=True):
        st.subheader("Mở kết quả đã lưu (replay)")
        uploaded = st.file_uploader(
            "Bundle JSON đã export", type=["json"], max_upload_size=30, key="replay_upload"
        )
        if st.button("Mở replay", disabled=uploaded is None) and uploaded is not None:
            try:
                session.bundle = load_bundle(uploaded.getvalue())
                session.sources = session.bundle.sources
                session.workspace.save(session.bundle)
            except (ResearchError, ValidationError, OSError):
                st.error(
                    "Không mở được bundle: schema/hash/locator/IDs không hợp lệ hoặc trùng bản đã lưu."
                )
