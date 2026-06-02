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


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate monthly apartment report markdown.")
    parser.add_argument("--lawd-cd", default="11500", help="법정동코드 앞 5자리")
    parser.add_argument("--deal-ym", required=True, help="계약년월 YYYYMM")
    parser.add_argument(
        "--all",
        action="store_true",
        help="월간 리포트, 상승률 리포트, 거래량 1위 단지 상세 리포트를 함께 생성합니다.",
    )
    args = parser.parse_args()

    settings = get_settings()
    conn = connect(settings.database_path)
    initialize(conn)
    report = analyze_month(conn, args.lawd_cd, args.deal_ym)
    persist_monthly_stats(conn, report)
    markdown = render_monthly_report(report)
    path = write_report(markdown, args.deal_ym, args.lawd_cd)
    print(path)

    if args.all:
        rising = render_top_rising_report(report)
        rising_path = write_markdown(rising, f"{args.deal_ym}_{args.lawd_cd}_top_rising_report.md")
        print(rising_path)

        if report.top_volume_complexes:
            item = report.top_volume_complexes[0]
            detail = render_apartment_detail_report(report, item)
            safe_name = safe_filename(item.apartment_name)
            detail_path = write_markdown(detail, f"{args.deal_ym}_{args.lawd_cd}_{safe_name}_detail_report.md")
            print(detail_path)


def safe_filename(value: str) -> str:
    allowed = []
    for char in value.strip():
        if char.isalnum() or char in ("-", "_"):
            allowed.append(char)
        elif char.isspace():
            allowed.append("_")
    return "".join(allowed) or "apartment"


if __name__ == "__main__":
    main()
