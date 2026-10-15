import calendar
import re
from datetime import date

from gamota_research.contracts import Dimension, ResearchRequest, SourceDocument


def period_bounds(period: str | None) -> tuple[date, date] | None:
    if not period:
        return None
    quarters = re.findall(r"(\d{4})-Q([1-4])", period)
    if quarters:
        first_year, first_quarter = map(int, quarters[0])
        last_year, last_quarter = map(int, quarters[-1])
        month = last_quarter * 3
        return (
            date(first_year, first_quarter * 3 - 2, 1),
            date(last_year, month, calendar.monthrange(last_year, month)[1]),
        )
    dates = re.findall(r"\d{4}-\d{2}-\d{2}", period)
    try:
        if dates:
            return date.fromisoformat(dates[0]), date.fromisoformat(dates[-1])
        if re.fullmatch(r"\d{4}-\d{2}", period):
            year, month = map(int, period.split("-"))
            return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])
    except ValueError:
        return None
    return None


def scope_dimension(request: ResearchRequest, source: SourceDocument) -> Dimension:
    known: list[bool] = []
    reasons: list[str] = []
    for label, wanted, available in [
        ("quốc gia", request.country, source.country),
        ("nền tảng", request.platforms, source.platforms),
    ]:
        if available:
            match = bool(set(map(str.casefold, wanted)) & set(map(str.casefold, available)))
            known.append(match)
            reasons.append(f"{label}: {'khớp' if match else 'khác'} metadata khai báo")
        else:
            reasons.append(f"{label}: unknown")
    value = "unknown"
    if False in known:
        value = "no"
    elif len(known) == len(reasons):
        value = "yes"
    elif known:
        value = "partial"
    return Dimension(value=value, rationale="; ".join(reasons), provenance="heuristic")


def freshness_dimension(request: ResearchRequest, source: SourceDocument) -> Dimension:
    bounds = period_bounds(source.data_period)
    if source.period_start and source.period_end:
        bounds = (source.period_start, source.period_end)
    if not bounds or not request.period_start or not request.period_end:
        return Dimension(rationale="Kỳ đo hoặc kỳ yêu cầu unknown; ngày đăng không thay kỳ đo.")
    start, end = bounds
    if end < request.period_start or start > request.period_end:
        return Dimension(value="no", rationale="Kỳ dữ liệu nằm ngoài kỳ nghiên cứu.")
    covered = start <= request.period_start and end >= request.period_end
    return Dimension(
        value="yes" if covered else "partial",
        rationale="Đối chiếu kỳ đo với kỳ yêu cầu; không dùng ngày xuất bản.",
    )
