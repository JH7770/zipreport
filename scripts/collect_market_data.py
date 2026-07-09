from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.analyzers.apartment_analyzer import RegionMarketBrief, analyze_region_market
from app.collectors.molit_rent_collector import MolitRentCollector
from app.collectors.molit_trade_collector import MolitTradeCollector
from app.collectors.reb_statistics_collector import RebStatisticsCollector
from app.collectors.region_code_collector import RegionCodeCollector
from app.config import PROJECT_ROOT, get_settings
from app.db.database import (
    connect,
    initialize,
    insert_reb_statistics,
    insert_rents,
    insert_trades,
    upsert_region_codes,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect sale, rent, REB, and region-code data for a market brief.")
    parser.add_argument("--lawd-cd", required=True, help="Legal district code prefix, e.g. 11500 for Seoul Gangseo-gu.")
    parser.add_argument("--deal-ym", required=True, help="Contract month in YYYYMM.")
    parser.add_argument("--region-keyword", help="Region keyword for code refresh, e.g. 서울특별시 강서구.")
    parser.add_argument("--skip-trade", action="store_true", help="Skip MOLIT apartment sale collection.")
    parser.add_argument("--skip-rent", action="store_true", help="Skip MOLIT apartment rent collection.")
    parser.add_argument("--reb-statbl-id", help="REB STATBL_ID to collect. Defaults to REB_STATBL_ID.")
    parser.add_argument("--reb-cycle", help="REB cycle code. Defaults to REB_CYCLE, usually MM or YY.")
    parser.add_argument("--reb-period", help="REB period. Defaults to --deal-ym.")
    parser.add_argument(
        "--reb-param",
        action="append",
        default=[],
        help="Extra REB query parameter in NAME=VALUE form. Repeat as needed.",
    )
    args = parser.parse_args()

    settings = get_settings()
    conn = connect(settings.database_path)
    initialize(conn)

    if args.region_keyword:
        regions = RegionCodeCollector(settings.public_data_api_key).search(args.region_keyword)
        changed = upsert_region_codes(conn, regions)
        print(f"Refreshed {changed} region rows from {len(regions)} region-code API rows.")

    if not args.skip_trade:
        trades = MolitTradeCollector(settings.public_data_api_key).fetch_month(args.lawd_cd, args.deal_ym)
        inserted = insert_trades(conn, trades)
        print(f"Fetched {len(trades)} sale trades, inserted {inserted} new rows.")

    if not args.skip_rent:
        rents = MolitRentCollector(settings.public_data_api_key).fetch_month(args.lawd_cd, args.deal_ym)
        inserted = insert_rents(conn, rents)
        print(f"Fetched {len(rents)} rent trades, inserted {inserted} new rows.")

    statbl_id = args.reb_statbl_id or settings.reb_statbl_id
    if statbl_id:
        reb_rows = RebStatisticsCollector(settings.reb_api_key).fetch_table(
            statbl_id=statbl_id,
            cycle=args.reb_cycle or settings.reb_cycle,
            period=args.reb_period or args.deal_ym,
            extra_params=_parse_params(args.reb_param),
        )
        inserted = insert_reb_statistics(conn, reb_rows)
        print(f"Fetched {len(reb_rows)} REB statistic rows, inserted {inserted} rows.")

    brief = analyze_region_market(conn, args.lawd_cd, args.deal_ym)
    output_path = write_market_brief(brief)
    print(output_path)


def write_market_brief(brief: RegionMarketBrief) -> Path:
    output_dir = PROJECT_ROOT / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{brief.deal_ym}_{brief.lawd_cd}_market_brief.md"
    path.write_text(_render_market_brief(brief), encoding="utf-8")
    return path


def _render_market_brief(brief: RegionMarketBrief) -> str:
    title = f"{brief.region_name} 아파트 매매가는 올랐는데 전세는 왜 약할까?"
    return "\n".join(
        [
            f"# {title}",
            "",
            "## 핵심 지표",
            "",
            f"- 매매 거래량: {_fmt_count(brief.sale_count)}",
            f"- 전월세 거래량: {_fmt_count(brief.rent_count)}",
            f"- 전세 거래량: {_fmt_count(brief.jeonse_count)}",
            f"- 평균 매매가: {_fmt_won(brief.avg_sale_amount)}",
            f"- 평균 전세보증금: {_fmt_won(brief.avg_jeonse_deposit)}",
            f"- 전세가율: {_fmt_percent(brief.jeonse_to_sale_ratio)}",
            "",
            "## 전월 대비 흐름",
            "",
            f"- 매매 거래량 변화율: {_fmt_percent(brief.sale_count_change_rate)}",
            f"- 매매가 변화율: {_fmt_percent(brief.sale_price_change_rate)}",
            f"- 전세보증금 변화율: {_fmt_percent(brief.jeonse_price_change_rate)}",
            "",
            "## 글감 메모",
            "",
            _market_note(brief),
            "",
        ]
    )


def _market_note(brief: RegionMarketBrief) -> str:
    if brief.sale_price_change_rate is not None and brief.sale_price_change_rate > 0:
        if brief.jeonse_price_change_rate is None:
            return "매매 쪽은 상승 신호가 있지만 전세 데이터가 부족합니다. 거래량과 단지별 샘플을 먼저 확인하세요."
        if brief.jeonse_price_change_rate <= 0:
            return "매매가는 올랐지만 전세보증금은 따라오지 못했습니다. 매수 기대와 임차 수요가 갈라졌는지 살펴볼 만합니다."
        if brief.jeonse_price_change_rate < brief.sale_price_change_rate:
            return "매매와 전세가 모두 올랐지만 매매 상승폭이 더 큽니다. 전세가율 하락 여부가 글의 중심축이 됩니다."
    return "매매가, 전세보증금, 거래량을 함께 놓고 수요의 온도 차이를 설명하는 방식으로 확장하세요."


def _parse_params(values: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Invalid --reb-param value: {value}")
        key, item = value.split("=", 1)
        parsed[key] = item
    return parsed


def _fmt_count(value: int | None) -> str:
    if value is None:
        return "데이터 없음"
    return f"{value:,}건"


def _fmt_percent(value: float | None) -> str:
    if value is None:
        return "데이터 없음"
    return f"{value:.1f}%"


def _fmt_won(value: int | None) -> str:
    if value is None:
        return "데이터 없음"
    if value >= 100000000:
        return f"{value / 100000000:.1f}억원"
    return f"{value:,}원"


if __name__ == "__main__":
    main()
