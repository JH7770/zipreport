from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.analyzers.apartment_analyzer import analyze_month, persist_monthly_stats
from app.config import get_settings
from app.db.database import connect, initialize
from app.generators.post_generator import (
    render_apartment_detail_report,
    render_monthly_report,
    render_top_rising_report,
    write_markdown,
    write_report,
)
from app.generators.llm_writer import LlmRewriteConfig, rewrite_markdown_with_llm
from app.generators.report_image import create_monthly_report_image
from app.quality.content_audit import audit_markdown_file, format_audit_result


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate monthly apartment report markdown.")
    parser.add_argument("--lawd-cd", default="11500", help="법정동코드 앞 5자리")
    parser.add_argument("--deal-ym", required=True, help="계약년월 YYYYMM")
    parser.add_argument(
        "--all",
        action="store_true",
        help="월간 리포트, 상승률 리포트, 거래량 1위 단지 상세 리포트를 함께 생성합니다.",
    )
    parser.add_argument("--use-llm", action="store_true", help="Rewrite generated Markdown with an LLM.")
    parser.add_argument("--generate-image", action="store_true", help="Generate a featured image for the monthly report.")
    parser.add_argument("--skip-audit", action="store_true", help="Skip generated Markdown quality audit.")
    args = parser.parse_args()

    settings = get_settings()
    conn = connect(settings.database_path)
    initialize(conn)
    report = analyze_month(conn, args.lawd_cd, args.deal_ym)
    persist_monthly_stats(conn, report)
    markdown = render_monthly_report(report)
    markdown = _maybe_rewrite(markdown, settings, args.use_llm, "monthly_region_report")
    path = write_report(markdown, args.deal_ym, args.lawd_cd)
    _audit_or_raise(path, args.skip_audit)
    print(path)

    if args.generate_image:
        image_path = create_monthly_report_image(report, args.lawd_cd)
        print(image_path)

    if args.all:
        rising = render_top_rising_report(report)
        rising = _maybe_rewrite(rising, settings, args.use_llm, "top_rising_report")
        rising_path = write_markdown(rising, f"{args.deal_ym}_{args.lawd_cd}_top_rising_report.md")
        _audit_or_raise(rising_path, args.skip_audit)
        print(rising_path)

        if report.top_volume_complexes:
            item = report.top_volume_complexes[0]
            detail = render_apartment_detail_report(report, item)
            detail = _maybe_rewrite(detail, settings, args.use_llm, "apartment_detail_report")
            safe_name = safe_filename(item.apartment_name)
            detail_path = write_markdown(detail, f"{args.deal_ym}_{args.lawd_cd}_{safe_name}_detail_report.md")
            _audit_or_raise(detail_path, args.skip_audit)
            print(detail_path)


def safe_filename(value: str) -> str:
    allowed = []
    for char in value.strip():
        if char.isalnum() or char in ("-", "_"):
            allowed.append(char)
        elif char.isspace():
            allowed.append("_")
    return "".join(allowed) or "apartment"


def _maybe_rewrite(markdown: str, settings: object, enabled: bool, report_type: str) -> str:
    if not enabled:
        return markdown
    return rewrite_markdown_with_llm(
        markdown,
        LlmRewriteConfig(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            base_url=settings.llm_base_url,
        ),
        report_type=report_type,
    )


def _audit_or_raise(path: Path, skip: bool) -> None:
    if skip:
        return
    result = audit_markdown_file(path)
    print(format_audit_result(result))
    if not result.passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
