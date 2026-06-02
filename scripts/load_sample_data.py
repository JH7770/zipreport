from __future__ import annotations

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.db.database import connect, initialize, insert_trades
from app.db.models import ApartmentTrade


def main() -> None:
    settings = get_settings()
    conn = connect(settings.database_path)
    initialize(conn)
    trades = _sample_trades()
    inserted = insert_trades(conn, trades)
    print(f"Loaded {inserted} sample trades.")


def _sample_trades() -> list[ApartmentTrade]:
    rows = [
        ("202604", 3, "마곡동", "마곡엠밸리7단지", 84.9, 1090000000, 8, 2014),
        ("202604", 8, "마곡동", "마곡엠밸리7단지", 84.9, 1110000000, 11, 2014),
        ("202604", 11, "등촌동", "등촌아이파크", 84.8, 865000000, 7, 2004),
        ("202604", 20, "염창동", "염창동아3차", 59.9, 720000000, 9, 1999),
        ("202605", 2, "마곡동", "마곡엠밸리7단지", 84.9, 1160000000, 10, 2014),
        ("202605", 9, "마곡동", "마곡엠밸리7단지", 84.9, 1175000000, 14, 2014),
        ("202605", 18, "마곡동", "마곡엠밸리7단지", 59.8, 935000000, 5, 2014),
        ("202605", 4, "등촌동", "등촌아이파크", 84.8, 902000000, 12, 2004),
        ("202605", 22, "등촌동", "등촌아이파크", 84.8, 918000000, 15, 2004),
        ("202605", 7, "염창동", "염창동아3차", 59.9, 752000000, 11, 1999),
        ("202605", 15, "화곡동", "우장산아이파크이편한세상", 84.9, 995000000, 13, 2008),
        ("202605", 24, "화곡동", "우장산아이파크이편한세상", 84.9, 1005000000, 18, 2008),
    ]
    return [
        ApartmentTrade(
            lawd_cd="11500",
            deal_ym=deal_ym,
            deal_day=day,
            dong=dong,
            apartment_name=name,
            exclusive_area=area,
            deal_amount=amount,
            floor=floor,
            build_year=build_year,
            raw_json="{}",
        )
        for deal_ym, day, dong, name, area, amount, floor, build_year in rows
    ]


if __name__ == "__main__":
    main()
