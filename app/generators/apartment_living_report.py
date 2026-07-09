from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.analyzers.apartment_living_analyzer import ApartmentLivingReport
from app.config import PROJECT_ROOT
from app.generators.post_generator import format_money, format_percent, write_markdown


def render_apartment_living_report(
    report: ApartmentLivingReport,
    template_name: str = "apartment_living_report.md",
) -> str:
    env = Environment(
        loader=FileSystemLoader(PROJECT_ROOT / "templates"),
        autoescape=select_autoescape(disabled_extensions=("md",)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["money"] = format_money
    env.filters["percent"] = format_percent
    env.filters["stars"] = format_stars
    env.filters["distance"] = format_distance
    env.filters["walk"] = walking_minutes
    env.filters["number"] = format_number
    return env.get_template(template_name).render(report=report)


def write_apartment_living_report(
    markdown: str,
    report: ApartmentLivingReport,
    deal_ym: str,
    lawd_cd: str,
    output_dir: Path | None = None,
) -> Path:
    safe_name = safe_filename(report.apartment_name)
    return write_markdown(
        markdown,
        f"{deal_ym}_{lawd_cd}_{safe_name}_living_report.md",
        output_dir,
    )


def safe_filename(value: str) -> str:
    chars = [char if char.isalnum() or char in ("-", "_") else "_" for char in value.strip()]
    return "".join(chars).strip("_") or "apartment"


def format_stars(value: int) -> str:
    score = max(0, min(5, int(value)))
    return "★" * score + "☆" * (5 - score)


def format_distance(value: int | None) -> str:
    if value is None:
        return "자료 없음"
    if value >= 1000:
        return f"{value / 1000:.1f}km"
    return f"{value}m"


def walking_minutes(value: int | None) -> str:
    if value is None:
        return "-"
    return f"약 {max(1, round(value / 75))}분"


def format_number(value: int | None) -> str:
    return f"{value:,}" if value is not None else "자료 없음"
