from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.collectors.ecos_collector import EcosCollector
from app.collectors.exim_exchange_collector import EximExchangeCollector
from app.collectors.kis_quote_collector import KisQuoteCollector
from app.collectors.naver_datalab_collector import NaverDatalabCollector
from app.config import get_settings
from app.db.database import (
    connect,
    initialize,
    insert_ecos_statistics,
    insert_exchange_rates,
    insert_search_trend_points,
    insert_stock_quotes,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect external macro, quote, and search trend data.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    exim = subparsers.add_parser("exim-exchange", help="Collect Korea Exim daily exchange rates.")
    exim.add_argument("--search-date", help="YYYYMMDD or YYYY-MM-DD. Defaults to Exim API current date.")

    ecos = subparsers.add_parser("ecos", help="Collect Bank of Korea ECOS statistics.")
    ecos.add_argument("--stat-code", required=True, help="ECOS statistic code, e.g. 731Y001.")
    ecos.add_argument("--cycle", required=True, help="ECOS cycle code, e.g. D, M, Q, A.")
    ecos.add_argument("--start-period", required=True, help="Start period, e.g. 202601 or 20260601.")
    ecos.add_argument("--end-period", required=True, help="End period, e.g. 202605 or 20260609.")
    ecos.add_argument("--item-code1")
    ecos.add_argument("--item-code2")
    ecos.add_argument("--item-code3")
    ecos.add_argument("--item-code4")

    kis = subparsers.add_parser("kis-quote", help="Collect KIS domestic stock quote.")
    kis.add_argument("--symbol", required=True, help="Domestic stock code, e.g. 005930.")
    kis.add_argument("--market", default="J", help="KIS market division code. Defaults to J.")

    naver = subparsers.add_parser("naver-trend", help="Collect Naver Datalab search trends.")
    naver.add_argument("--start-date", required=True, help="YYYY-MM-DD.")
    naver.add_argument("--end-date", required=True, help="YYYY-MM-DD.")
    naver.add_argument("--time-unit", default="date", choices=["date", "week", "month"])
    naver.add_argument(
        "--group",
        action="append",
        required=True,
        help='Keyword group as "title=keyword1,keyword2". Repeat for multiple groups.',
    )

    args = parser.parse_args()
    settings = get_settings()
    conn = connect(settings.database_path)
    initialize(conn)

    if args.command == "exim-exchange":
        rows = EximExchangeCollector(settings.exim_api_key).fetch_daily(args.search_date)
        print(f"Fetched {len(rows)} exchange-rate rows, inserted {insert_exchange_rates(conn, rows)} rows.")
    elif args.command == "ecos":
        rows = EcosCollector(settings.ecos_api_key).fetch_statistic_search(
            stat_code=args.stat_code,
            cycle=args.cycle,
            start_period=args.start_period,
            end_period=args.end_period,
            item_code1=args.item_code1,
            item_code2=args.item_code2,
            item_code3=args.item_code3,
            item_code4=args.item_code4,
        )
        print(f"Fetched {len(rows)} ECOS rows, inserted {insert_ecos_statistics(conn, rows)} rows.")
    elif args.command == "kis-quote":
        row = KisQuoteCollector(
            settings.kis_app_key,
            settings.kis_app_secret,
            base_url=settings.kis_base_url,
        ).fetch_domestic_price(args.symbol, args.market)
        print(f"Fetched 1 KIS quote row, inserted {insert_stock_quotes(conn, [row])} rows.")
    elif args.command == "naver-trend":
        rows = NaverDatalabCollector(
            settings.naver_client_id,
            settings.naver_client_secret,
        ).fetch_search_trends(
            start_date=args.start_date,
            end_date=args.end_date,
            time_unit=args.time_unit,
            keyword_groups=_parse_keyword_groups(args.group),
        )
        print(f"Fetched {len(rows)} Naver trend rows, inserted {insert_search_trend_points(conn, rows)} rows.")


def _parse_keyword_groups(values: list[str]) -> list[dict[str, object]]:
    groups: list[dict[str, object]] = []
    for value in values:
        if "=" not in value:
            raise ValueError(f"Invalid --group value: {value}")
        title, keywords = value.split("=", 1)
        group_keywords = [keyword.strip() for keyword in keywords.split(",") if keyword.strip()]
        if not title.strip() or not group_keywords:
            raise ValueError(f"Invalid --group value: {value}")
        groups.append({"groupName": title.strip(), "keywords": group_keywords})
    return groups


if __name__ == "__main__":
    main()
