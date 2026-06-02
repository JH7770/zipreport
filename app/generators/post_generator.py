from __future__ import annotations

from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:  # pragma: no cover - exercised in dependency-free environments.
    Environment = None
    FileSystemLoader = None
    select_autoescape = None

from app.analyzers.apartment_analyzer import ComplexStat, RegionReport
from app.config import PROJECT_ROOT


def _build_environment() -> Environment | None:
    if Environment is None or FileSystemLoader is None or select_autoescape is None:
        return None
    env = Environment(
        loader=FileSystemLoader(PROJECT_ROOT / "templates"),
        autoescape=select_autoescape(disabled_extensions=("md",)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["money"] = format_money
    env.filters["percent"] = format_percent
    env.filters["ym"] = format_deal_ym
    return env


def render_monthly_report(report: RegionReport, template_name: str = "monthly_region_report.md") -> str:
    env = _build_environment()
    if env is None:
        return render_monthly_report_fallback(report)
    template = env.get_template(template_name)
    return template.render(report=report)


def render_top_rising_report(report: RegionReport, template_name: str = "top_rising_report.md") -> str:
    env = _build_environment()
    if env is None:
        return render_top_rising_report_fallback(report)
    template = env.get_template(template_name)
    return template.render(report=report)


def render_apartment_detail_report(
    report: RegionReport,
    complex_stat: ComplexStat,
    template_name: str = "apartment_detail_report.md",
) -> str:
    env = _build_environment()
    if env is None:
        return render_apartment_detail_report_fallback(report, complex_stat)
    template = env.get_template(template_name)
    return template.render(report=report, item=complex_stat)


def render_monthly_report_fallback(report: RegionReport) -> str:
    lines = [
        f"# {format_deal_ym(report.deal_ym)} {report.region_name} 아파트 실거래가 리포트",
        "",
        (
            f"{format_deal_ym(report.deal_ym)} {report.region_name} 아파트 매매 실거래는 "
            f"총 {report.total_count}건으로 집계되었습니다. 전월 {report.prev_total_count}건과 비교하면 "
            f"거래량 변화율은 {format_percent(report.count_change_rate)}입니다."
        ),
        "",
        "## 핵심 요약",
        "",
        f"- 총 거래 건수: {report.total_count}건",
        f"- 전월 대비 거래량 변화: {format_percent(report.count_change_rate)}",
        f"- 평균 거래가: {format_money(report.avg_deal_amount)}",
        f"- 전월 평균 거래가: {format_money(report.prev_avg_deal_amount)}",
        f"- 평균 거래가 변화: {format_percent(report.avg_change_rate)}",
        "",
        "## 거래량 TOP 10 단지",
        "",
        "| 순위 | 단지명 | 법정동 | 면적 | 거래 건수 | 평균 거래가 | 평당가 |",
        "|---:|---|---|---:|---:|---:|---:|",
    ]

    for index, item in enumerate(report.top_volume_complexes, 1):
        lines.append(
            f"| {index} | {item.apartment_name} | {item.dong or '-'} | "
            f"{item.exclusive_area_group or '-'} | {item.trade_count} | "
            f"{format_money(item.avg_deal_amount)} | {format_money(item.avg_price_per_pyeong)} |"
        )

    lines.extend(
        [
            "",
            "## 전월 대비 상승 단지",
            "",
            "| 순위 | 단지명 | 법정동 | 면적 | 전월 평균 | 이번 달 평균 | 변화율 |",
            "|---:|---|---|---:|---:|---:|---:|",
        ]
    )
    if report.top_rising_complexes:
        for index, item in enumerate(report.top_rising_complexes, 1):
            lines.append(
                f"| {index} | {item.apartment_name} | {item.dong or '-'} | "
                f"{item.exclusive_area_group or '-'} | {format_money(item.prev_avg_deal_amount)} | "
                f"{format_money(item.avg_deal_amount)} | {format_percent(item.price_change_rate)} |"
            )
    else:
        lines.append("| - | 전월과 직접 비교 가능한 단지가 부족합니다. | - | - | - | - | - |")

    lines.extend(
        [
            "",
            "## 신고가 후보 단지",
            "",
            "최근 집계 기준 최고 거래금액이 높은 단지입니다. 실제 신고가 여부는 해제 거래, 면적, 층, 이전 거래 이력에 따라 달라질 수 있습니다.",
            "",
            "| 순위 | 단지명 | 법정동 | 면적 | 최고 거래가 | 최저 거래가 |",
            "|---:|---|---|---:|---:|---:|",
        ]
    )
    for index, item in enumerate(report.record_high_complexes, 1):
        lines.append(
            f"| {index} | {item.apartment_name} | {item.dong or '-'} | "
            f"{item.exclusive_area_group or '-'} | {format_money(item.max_deal_amount)} | "
            f"{format_money(item.min_deal_amount)} |"
        )

    lines.extend(
        [
            "",
            "## 참고 사항",
            "",
            "본 글은 국토교통부 공공데이터 API 기반의 신고 자료를 정리한 참고용 리포트입니다. 거래 신고와 정정, 해제 처리 시점에 따라 수치는 달라질 수 있으며, 매수 또는 매도 추천으로 해석해서는 안 됩니다.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_report(markdown: str, deal_ym: str, lawd_cd: str, output_dir: Path | None = None) -> Path:
    return write_markdown(markdown, f"{deal_ym}_{lawd_cd}_monthly_report.md", output_dir)


def write_markdown(markdown: str, filename: str, output_dir: Path | None = None) -> Path:
    directory = output_dir or PROJECT_ROOT / "output"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    path.write_text(markdown, encoding="utf-8")
    return path


def render_top_rising_report_fallback(report: RegionReport) -> str:
    lines = [
        f"# {format_deal_ym(report.deal_ym)} {report.region_name} 아파트 상승률 TOP 10",
        "",
        f"{report.region_name}에서 전월과 같은 단지·면적으로 비교 가능한 거래를 기준으로 상승률이 높은 단지를 정리했습니다.",
        "",
        "| 순위 | 단지명 | 법정동 | 면적 | 전월 평균 | 이번 달 평균 | 변화율 |",
        "|---:|---|---|---:|---:|---:|---:|",
    ]
    if report.top_rising_complexes:
        for index, item in enumerate(report.top_rising_complexes, 1):
            lines.append(
                f"| {index} | {item.apartment_name} | {item.dong or '-'} | "
                f"{item.exclusive_area_group or '-'} | {format_money(item.prev_avg_deal_amount)} | "
                f"{format_money(item.avg_deal_amount)} | {format_percent(item.price_change_rate)} |"
            )
    else:
        lines.append("| - | 전월과 직접 비교 가능한 단지가 부족합니다. | - | - | - | - | - |")

    lines.extend(
        [
            "",
            "## 해석 기준",
            "",
            "상승률은 같은 단지명과 같은 전용면적 기준의 전월 평균 거래가 대비 이번 달 평균 거래가 변화율입니다. 거래가 1건뿐인 단지는 표본이 작으므로 참고 자료로만 보는 것이 좋습니다.",
            "",
            "본 글은 투자 권유가 아닌 공공데이터 기반 참고 자료입니다.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_apartment_detail_report_fallback(report: RegionReport, item: ComplexStat) -> str:
    lines = [
        f"# {format_deal_ym(report.deal_ym)} {item.apartment_name} 실거래가 요약",
        "",
        f"{report.region_name} {item.dong or ''}의 {item.apartment_name} {item.exclusive_area_group or ''} 거래를 정리했습니다.",
        "",
        "## 거래 요약",
        "",
        f"- 거래 건수: {item.trade_count}건",
        f"- 평균 거래가: {format_money(item.avg_deal_amount)}",
        f"- 최저 거래가: {format_money(item.min_deal_amount)}",
        f"- 최고 거래가: {format_money(item.max_deal_amount)}",
        f"- 평균 평당가: {format_money(item.avg_price_per_pyeong)}",
        f"- 전월 평균 거래가: {format_money(item.prev_avg_deal_amount)}",
        f"- 전월 대비 변화율: {format_percent(item.price_change_rate)}",
        "",
        "## 참고 사항",
        "",
        "같은 단지라도 층, 향, 동, 수리 상태, 거래 시점에 따라 가격 차이가 발생할 수 있습니다. 이 글은 공공데이터를 정리한 참고 자료이며 매수 또는 매도 추천이 아닙니다.",
    ]
    return "\n".join(lines) + "\n"


def format_money(value: int | None) -> str:
    if value is None:
        return "-"
    eok = value // 100000000
    man = (value % 100000000) // 10000
    if eok and man:
        return f"{eok}억 {man:,}만원"
    if eok:
        return f"{eok}억원"
    return f"{man:,}만원"


def format_percent(value: float | None) -> str:
    if value is None:
        return "-"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.1f}%"


def format_deal_ym(value: str) -> str:
    return f"{value[:4]}년 {int(value[4:]):02d}월"
