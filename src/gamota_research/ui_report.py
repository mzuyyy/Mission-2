import streamlit as st

from gamota_research.contracts import Claim, Evidence, ReviewDecision, SourceDocument
from gamota_research.export import export_markdown
from gamota_research.models import ReportBundle
from gamota_research.storage import review
from gamota_research.ui_state import Session


def show_evidence(evidence: Evidence, sources: list[SourceDocument], key: str) -> None:
    source = next(s for s in sources if s.source_id == evidence.source_id)
    st.caption(
        f"{evidence.evidence_id} · {source.source_id} · trang {evidence.page_number or 'N/A'} · "
        f"ký tự [{evidence.start_char}, {evidence.end_char})"
    )
    st.text(source.display_title)
    st.code(evidence.quote, language=None, wrap_lines=True)
    st.caption("Ngữ cảnh từ snapshot bất biến")
    st.text(source.normalized_text[max(0, evidence.start_char - 250) : evidence.end_char + 250])
    st.caption(f"SHA-256: {source.content_hash}")
    if source.original_url and source.original_url.startswith(("https://", "http://")):
        st.link_button("Mở nguồn gốc bên ngoài", source.original_url, key=key)
    st.caption("Quote khớp không chứng minh nhận định đúng. Hãy kiểm tra ý nghĩa và phạm vi.")


def show_claim_evidence(claim: Claim, bundle: ReportBundle, key: str) -> None:
    by_eid = {e.evidence_id: e for e in bundle.report.evidence}
    if not claim.evidence_links:
        st.info("Chưa có evidence trực tiếp. Xem premises/giả định và dữ liệu cần bổ sung.")
    for index, link in enumerate(claim.evidence_links):
        st.caption(f"Quan hệ do model đề xuất: {link.relation}")
        show_evidence(by_eid[link.evidence_id], bundle.sources, f"{key}_{claim.claim_id}_{index}")


def results(bundle: ReportBundle) -> None:
    report = bundle.report
    st.subheader("Nhận định trong phạm vi đã chốt")
    st.text(report.request.question)
    if not report.claims:
        st.info("Chưa đủ bằng chứng để tạo nhận định; xem dữ liệu còn thiếu.")
    for claim in report.claims:
        show_claim(claim, bundle)
    st.subheader("Mâu thuẫn và khác phạm vi")
    if not report.conflicts:
        st.caption("Model chưa nêu mâu thuẫn; không đồng nghĩa đã chứng minh không có mâu thuẫn.")
    for conflict in report.conflicts:
        st.text(
            f"{conflict.conflict_id}: same_scope={conflict.same_scope}, unresolved={conflict.unresolved}"
        )
        st.text(conflict.explanation)
        st.json(conflict.comparison_dimensions.model_dump())
    st.subheader("Hành động có điều kiện")
    for recommendation in report.recommendations:
        if recommendation.blocked:
            st.warning(f"{recommendation.recommendation_id}: Chưa đủ điều kiện thực hiện lựa chọn.")
        st.text(recommendation.action)
        st.text("Lý do: " + recommendation.rationale)
        st.text("Điều kiện: " + "; ".join(recommendation.conditions))
        st.text("Chặn bởi: " + "; ".join(recommendation.blocking_unknowns))
        st.text("Bước bổ sung dữ liệu: " + recommendation.next_step)
    st.subheader("Thông tin còn thiếu")
    for missing in report.missing_data:
        st.text(missing)


def sources_view(sources: list[SourceDocument], bundle: ReportBundle | None) -> None:
    if not sources:
        st.info("Nhập URL/PDF hoặc nạp fixture để xem nguồn offline.")
    for source in sources:
        with st.expander(
            f"{source.source_id} · {source.read_status}", expanded=source.read_status != "ok"
        ):
            st.text(source.display_title)
            if source.read_error:
                st.warning(source.read_error)
            st.caption("DỮ LIỆU GIẢ LẬP" if source.is_synthetic else "Nguồn được cung cấp")
            st.json(source.model_dump(mode="json", exclude={"normalized_text", "pages"}))
            st.code(source.normalized_text, language=None, wrap_lines=True)
            if bundle:
                for assessment in bundle.report.assessments:
                    if assessment.source_id == source.source_id:
                        st.json(assessment.model_dump())


def review_view(session: Session) -> None:
    bundle = session.bundle
    if bundle is None:
        st.info("Sinh hoặc mở report đã lưu để đánh giá nhận định.")
        return
    report = bundle.report
    if report.claims:
        claim_id = st.selectbox("Nhận định cần đánh giá", [c.claim_id for c in report.claims])
        claim = next(c for c in report.claims if c.claim_id == claim_id)
        with st.form(f"review_{report.report_id}_{report.version}_{claim_id}"):
            decision: ReviewDecision = st.selectbox(
                "Đánh giá của bạn", ["accept", "needs_review", "reject"], index=1
            )
            note = st.text_area("Ghi chú đánh giá")
            edited = st.text_area("Nội dung nhận định (có thể sửa)", value=claim.text)
            submitted = st.form_submit_button("Lưu đánh giá thành phiên bản mới")
        if submitted:
            updated = review(bundle, claim_id, decision, note, edited)
            session.workspace.save(updated)
            session.bundle = updated
            st.success(f"Đã lưu version {updated.report.version}; giữ snapshot trước và sau.")
            st.rerun()
    st.caption(
        "Accept là ý kiến của người dùng, không phải kiểm định tự động. Sửa nội dung cần chấm lại support."
    )
    st.json([event.model_dump(mode="json") for event in report.review_history])


def report_tabs(session: Session) -> None:
    bundle = session.bundle
    if bundle:
        report = bundle.report
        if report.is_synthetic:
            st.warning("DỮ LIỆU GIẢ LẬP: chỉ kiểm tra logic, không phải nghiên cứu thị trường.")
        if report.mode == "replay":
            st.info(
                f"REPLAY · kết quả đã lưu lúc {report.generated_at.isoformat()}, không phải lượt live mới."
            )
        st.caption(
            f"Mode {report.mode} · version {report.version} · model {report.model_id} · prompt {report.prompt_version}"
        )
        st.download_button(
            "Xuất JSON và snapshot nguồn",
            bundle.model_dump_json(indent=2),
            file_name=f"report_{report.report_id}_v{report.version}.json",
            mime="application/json",
        )
        st.download_button(
            "Xuất Markdown",
            export_markdown(bundle),
            file_name=f"report_{report.report_id}_v{report.version}.md",
            mime="text/markdown",
        )
    result_tab, evidence_tab, source_tab, check_tab = st.tabs(
        ["Kết quả", "Bằng chứng", "Nguồn", "Kiểm tra"], key="report_tabs"
    )
    with result_tab:
        if bundle:
            results(bundle)
        else:
            st.info("Chưa có nhận định. Đọc nguồn offline hoặc cấu hình LLM tại máy để sinh live.")
    with evidence_tab:
        if bundle and bundle.report.claims:
            claim_id = st.selectbox(
                "Chọn nhận định để mở đúng đoạn nguồn", [c.claim_id for c in bundle.report.claims]
            )
            show_claim_evidence(
                next(c for c in bundle.report.claims if c.claim_id == claim_id), bundle, "evidence"
            )
        else:
            st.caption("Chưa có evidence/claim LLM. Snapshot gốc vẫn xem được trong tab Nguồn.")
    with source_tab:
        sources_view(session.sources, bundle)
    with check_tab:
        if bundle:
            st.json(bundle.report.coverage.model_dump())
            st.json(bundle.report.validation.model_dump())
            st.json(bundle.report.usage.model_dump())
        review_view(session)


def show_claim(claim: Claim, bundle: ReportBundle) -> None:
    with st.container(border=True):
        st.caption(
            f"{claim.claim_id} · {claim.kind} · {claim.assessment} · review: {claim.human_review}"
        )
        st.text(claim.text)
        if claim.premise_claim_ids:
            st.text("Premises: " + ", ".join(claim.premise_claim_ids))
        if claim.reasoning:
            st.text("Lập luận: " + claim.reasoning)
        for label, items in [
            ("Giả định", claim.assumptions),
            ("Giới hạn", claim.limitations),
            ("Còn thiếu", claim.missing_data),
        ]:
            if items:
                st.text(label + ": " + "; ".join(items))
        with st.expander(f"Mở bằng chứng {claim.claim_id}"):
            show_claim_evidence(claim, bundle, "result")
