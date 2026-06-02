from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.collectors.molit_trade_collector import MolitTradeCollector
from app.config import get_settings
from app.db.database import connect, initialize, insert_trades


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect apartment trade data from MOLIT open API.")
    parser.add_argument("--lawd-cd", default="11500", help="법정동코드 앞 5자리. 기본값: 서울 강서구 11500")
    parser.add_argument("--deal-ym", required=True, help="계약년월 YYYYMM")
    parser.add_argument("--detail-api", action="store_true", help="상세 자료 API 엔드포인트 사용")
    args = parser.parse_args()

    settings = get_settings()
    collector = MolitTradeCollector(settings.public_data_api_key)
    if args.detail_api:
        from app.collectors.molit_trade_collector import DETAIL_ENDPOINT

        collector.endpoint = DETAIL_ENDPOINT

    conn = connect(settings.database_path)
    initialize(conn)
    trades = collector.fetch_month(args.lawd_cd, args.deal_ym)
    inserted = insert_trades(conn, trades)
    print(f"Fetched {len(trades)} trades, inserted {inserted} new rows.")


if __name__ == "__main__":
    main()
