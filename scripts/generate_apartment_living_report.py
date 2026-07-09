from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.analyzers.apartment_analyzer import previous_month
from app.collectors.molit_trade_collector import MolitTradeCollector
from app.config import get_settings
from app.db.database import connect, initialize, insert_trades, save_wordpress_post
from app.generators.apartment_living_report import (
    render_apartment_living_report,
    write_apartment_living_report,
)
from app.generators.llm_writer import LlmRewriteConfig, rewrite_markdown_with_llm
from app.publishers.wordpress_publisher import WordpressPublisher, extract_title
from app.services.apartment_living_report_service import build_apartment_living_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an apartment living-infrastructure report.")
    parser.add_argument("--apartment", required=True, help="아파트 단지명")
    parser.add_argument("--lawd-cd", required=True, help="법정동코드 앞 5자리")
    parser.add_argument("--deal-ym", required=True, help="실거래 기준월 YYYYMM")
    parser.add_argument("--radius", type=int, default=1000, help="생활권 반경(m), 기본값 1000")
    parser.add_argument("--snapshot-date", help="상가 스냅샷 날짜 YYYY-MM-DD")
    parser.add_argument("--transit-date", help="서울 지하철 승하차 기준일 YYYYMMDD")
    parser.add_argument("--longitude", type=float, help="카카오 로컬을 사용할 수 없을 때 적용할 경도")
    parser.add_argument("--latitude", type=float, help="카카오 로컬을 사용할 수 없을 때 적용할 위도")
    parser.add_argument("--address", help="단지 주소")
    parser.add_argument("--station-name", help="최근접 지하철역 이름")
    parser.add_argument("--station-distance", type=int, help="최근접 지하철역 직선/지도 거리(m)")
    parser.add_argument("--school-name", action="append", default=[], help="나이스로 보강할 인근 학교명")
    parser.add_argument("--collect-trades", action="store_true", help="당월과 전월 실거래를 먼저 수집")
    parser.add_argument("--use-llm", action="store_true", help="숫자를 유지한 채 LLM으로 문장을 윤문")
    parser.add_argument("--publish", action="store_true", help="생성한 글을 WordPress에 발행")
    parser.add_argument("--status", help="WordPress 상태, 기본값은 DEFAULT_STATUS")
    parser.add_argument("--category", action="append", type=int, default=[], help="WordPress category ID")
    parser.add_argument("--tag", action="append", type=int, default=[], help="WordPress tag ID")
    args = parser.parse_args()

    if args.radius < 100 or args.radius > 20000:
        parser.error("--radius는 카카오 로컬 API 범위인 100~20000m로 지정해야 합니다.")

    settings = get_settings()
    conn = connect(settings.database_path)
    initialize(conn)

    if args.collect_trades:
        collector = MolitTradeCollector(settings.public_data_api_key)
        for deal_ym in (previous_month(args.deal_ym), args.deal_ym):
            insert_trades(conn, collector.fetch_month(args.lawd_cd, deal_ym))

    report = build_apartment_living_report(
        conn,
        settings,
        apartment_name=args.apartment,
        lawd_cd=args.lawd_cd,
        deal_ym=args.deal_ym,
        radius_m=args.radius,
        snapshot_date=args.snapshot_date,
        transit_date=args.transit_date,
        longitude=args.longitude,
        latitude=args.latitude,
        address=args.address,
        station_name=args.station_name,
        station_distance_m=args.station_distance,
        school_names=args.school_name,
    )
    markdown = render_apartment_living_report(report)
    if args.use_llm:
        markdown = rewrite_markdown_with_llm(
            markdown,
            LlmRewriteConfig(settings.llm_api_key, settings.llm_model, settings.llm_base_url),
            report_type="apartment_living_report",
        )
    path = write_apartment_living_report(markdown, report, args.deal_ym, args.lawd_cd)
    print(path)

    if args.publish:
        publisher = WordpressPublisher(
            settings.wordpress_url,
            settings.wordpress_username,
            settings.wordpress_app_password,
        )
        result = publisher.publish_markdown_file(
            path,
            status=args.status or settings.default_status,
            categories=args.category,
            tags=args.tag,
        )
        save_wordpress_post(
            conn,
            post_type="apartment_living_report",
            region=report.address or args.lawd_cd,
            deal_ym=args.deal_ym,
            title=extract_title(markdown),
            wordpress_post_id=result.post_id,
            status=result.status,
        )
        print(result.link or result.post_id)


if __name__ == "__main__":
    main()
