from gamota_research.models import ReportBundle


def plain_markdown(text: str) -> str:
    """Neutralize active HTML/links in untrusted prose while retaining readable text."""
    for character in "\\`*_{}[]<>#|!":
        text = text.replace(character, "\\" + character)
    return text


def export_markdown(bundle: ReportBundle) -> str:
    report = bundle.report
    lines = [
        "# Báo cáo nghiên cứu",
        "",
        plain_markdown(report.request.question),
        "",
        f"Mode: {report.mode}; version: {report.version}; model: {report.model_id}; prompt: {report.prompt_version}",
        f"Thời điểm gốc: {report.generated_at.isoformat()}",
        "",
        "DỮ LIỆU GIẢ LẬP" if report.is_synthetic else "Nguồn do người dùng cung cấp.",
        "Locator đã kiểm tra không đồng nghĩa hỗ trợ ngữ nghĩa đã được xác minh.",
        "",
        "## Nhận định",
        "",
    ]
    for claim in report.claims:
        lines.extend(
            [
                f"### {claim.claim_id} [{claim.kind}; {claim.assessment}; {claim.human_review}]",
                "",
                plain_markdown(claim.text),
                "",
            ]
        )
        lines.extend(
            f"- {link.relation}: [{link.evidence_id}](#{link.evidence_id.lower()})"
            for link in claim.evidence_links
        )
        lines.extend(
            [
                f"- Premises: {', '.join(claim.premise_claim_ids) or 'N/A'}",
                f"- Lập luận: {plain_markdown(claim.reasoning or 'N/A')}",
                f"- Giả định: {plain_markdown('; '.join(claim.assumptions) or 'N/A')}",
                f"- Giới hạn: {plain_markdown('; '.join(claim.limitations) or 'unknown')}",
                f"- Thiếu: {plain_markdown('; '.join(claim.missing_data) or 'Chưa nêu thêm')}",
                "",
            ]
        )
    lines.extend(["## Bằng chứng", ""])
    by_sid = {source.source_id: source for source in bundle.sources}
    for evidence in report.evidence:
        source = by_sid[evidence.source_id]
        lines.extend(
            [
                f"### {evidence.evidence_id}",
                "",
                plain_markdown(evidence.quote),
                "",
                f"Nguồn {evidence.source_id}: {plain_markdown(source.display_title)}",
                f"URL: {plain_markdown(source.original_url or source.local_name or 'fixture')}",
                f"Locator: [{evidence.start_char}, {evidence.end_char}); trang {evidence.page_number or 'N/A'}",
                f"SHA-256: {evidence.content_hash}",
                "",
                "Ngữ cảnh: " + plain_markdown(evidence.surrounding_context),
                "",
            ]
        )
    lines.extend(["## Hành động", ""])
    for recommendation in report.recommendations:
        lines.extend(
            [
                f"- {recommendation.recommendation_id}: {plain_markdown(recommendation.action)}; blocked={recommendation.blocked}",
                "  - Lý do: " + plain_markdown(recommendation.rationale),
                "  - Điều kiện: " + plain_markdown("; ".join(recommendation.conditions)),
                "  - Chặn bởi: " + plain_markdown("; ".join(recommendation.blocking_unknowns)),
                "  - Bước tiếp: " + plain_markdown(recommendation.next_step),
            ]
        )
    for heading, values in [
        ("Mâu thuẫn/khác phạm vi", [c.model_dump_json() for c in report.conflicts]),
        ("Thông tin còn thiếu", report.missing_data),
        ("Coverage", [report.coverage.model_dump_json()]),
        ("Đánh giá nguồn", [a.model_dump_json() for a in report.assessments]),
        ("Review history", [r.model_dump_json() for r in report.review_history]),
    ]:
        lines.extend(["", f"## {heading}", "", *(plain_markdown(v) for v in values)])
    lines.extend(["", "JSON đi kèm chứa snapshot nguồn bất biến để kiểm tra và replay."])
    return "\n".join(lines)
