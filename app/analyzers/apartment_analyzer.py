from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime

from app.config import REGIONS


PYEONG_IN_SQUARE_METERS = 3.3058


@dataclass(frozen=True)
class ComplexStat:
    apartment_name: str
    dong: str | None
    exclusive_area_group: str | None
    trade_count: int
    avg_deal_amount: int
    min_deal_amount: int
    max_deal_amount: int
    avg_price_per_pyeong: int | None
    prev_avg_deal_amount: int | None
    price_change_rate: float | None


@dataclass(frozen=True)
class RegionReport:
    lawd_cd: str
    region_name: str
    deal_ym: str
    prev_deal_ym: str
    total_count: int
    prev_total_count: int
    count_change_rate: float | None
    avg_deal_amount: int | None
    prev_avg_deal_amount: int | None
    avg_change_rate: float | None
    top_volume_complexes: list[ComplexStat]
    top_rising_complexes: list[ComplexStat]
    record_high_complexes: list[ComplexStat]


def analyze_month(conn: sqlite3.Connection, lawd_cd: str, deal_ym: str) -> RegionReport:
    prev_deal_ym = previous_month(deal_ym)
    current = _month_summary(conn, lawd_cd, deal_ym)
    previous = _month_summary(conn, lawd_cd, prev_deal_ym)
    complex_stats = _complex_stats(conn, lawd_cd, deal_ym, prev_deal_ym)

    top_volume = sorted(complex_stats, key=lambda row: row.trade_count, reverse=True)[:10]
    top_rising = [
        row
        for row in sorted(
            complex_stats,
            key=lambda row: row.price_change_rate if row.price_change_rate is not None else -999999,
            reverse=True,
        )
        if row.price_change_rate is not None
    ][:10]
    record_high = sorted(complex_stats, key=lambda row: row.max_deal_amount, reverse=True)[:10]

    region = REGIONS.get(lawd_cd, {"sido": "", "sigungu": lawd_cd})
    return RegionReport(
        lawd_cd=lawd_cd,
        region_name=f"{region['sido']} {region['sigungu']}".strip(),
        deal_ym=deal_ym,
        prev_deal_ym=prev_deal_ym,
        total_count=current["count"],
        prev_total_count=previous["count"],
        count_change_rate=change_rate(current["count"], previous["count"]),
        avg_deal_amount=current["avg"],
        prev_avg_deal_amount=previous["avg"],
        avg_change_rate=change_rate(current["avg"], previous["avg"]),
        top_volume_complexes=top_volume,
        top_rising_complexes=top_rising,
        record_high_complexes=record_high,
    )


def persist_monthly_stats(conn: sqlite3.Connection, report: RegionReport) -> None:
    conn.execute(
        "DELETE FROM apartment_monthly_stats WHERE lawd_cd = ? AND deal_ym = ?",
        (report.lawd_cd, report.deal_ym),
    )
    for row in report.top_volume_complexes:
        conn.execute(
            """
            INSERT INTO apartment_monthly_stats (
                lawd_cd, deal_ym, apartment_name, dong, exclusive_area_group,
                trade_count, avg_deal_amount, min_deal_amount, max_deal_amount,
                avg_price_per_pyeong, prev_avg_deal_amount, price_change_rate
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report.lawd_cd,
                report.deal_ym,
                row.apartment_name,
                row.dong,
                row.exclusive_area_group,
                row.trade_count,
                row.avg_deal_amount,
                row.min_deal_amount,
                row.max_deal_amount,
                row.avg_price_per_pyeong,
                row.prev_avg_deal_amount,
                row.price_change_rate,
            ),
        )
    conn.commit()


def previous_month(deal_ym: str) -> str:
    dt = datetime.strptime(deal_ym, "%Y%m")
    year = dt.year
    month = dt.month - 1
    if month == 0:
        year -= 1
        month = 12
    return f"{year}{month:02d}"


def change_rate(current: int | float | None, previous: int | float | None) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return round((current - previous) / previous * 100, 1)


def area_group(area: float | None) -> str | None:
    if area is None:
        return None
    return f"{round(area, 1):.1f}m2"


def price_per_pyeong(deal_amount: int | None, area: float | None) -> int | None:
    if deal_amount is None or not area:
        return None
    pyeong = area / PYEONG_IN_SQUARE_METERS
    return int(round(deal_amount / pyeong))


def _month_summary(conn: sqlite3.Connection, lawd_cd: str, deal_ym: str) -> dict[str, int | None]:
    row = conn.execute(
        """
        SELECT COUNT(*) AS trade_count, ROUND(AVG(deal_amount)) AS avg_amount
        FROM apartment_trade
        WHERE lawd_cd = ? AND deal_ym = ? AND deal_amount IS NOT NULL
        """,
        (lawd_cd, deal_ym),
    ).fetchone()
    return {"count": int(row["trade_count"] or 0), "avg": int(row["avg_amount"]) if row["avg_amount"] else None}


def _complex_stats(conn: sqlite3.Connection, lawd_cd: str, deal_ym: str, prev_deal_ym: str) -> list[ComplexStat]:
    current_rows = conn.execute(
        """
        SELECT
            apartment_name,
            dong,
            ROUND(exclusive_area, 1) AS area,
            COUNT(*) AS trade_count,
            ROUND(AVG(deal_amount)) AS avg_deal_amount,
            MIN(deal_amount) AS min_deal_amount,
            MAX(deal_amount) AS max_deal_amount,
            ROUND(AVG(deal_amount / (exclusive_area / ?))) AS avg_price_per_pyeong
        FROM apartment_trade
        WHERE lawd_cd = ? AND deal_ym = ? AND deal_amount IS NOT NULL
        GROUP BY apartment_name, dong, ROUND(exclusive_area, 1)
        HAVING COUNT(*) >= 1
        """,
        (PYEONG_IN_SQUARE_METERS, lawd_cd, deal_ym),
    ).fetchall()

    stats: list[ComplexStat] = []
    for row in current_rows:
        prev = conn.execute(
            """
            SELECT ROUND(AVG(deal_amount)) AS avg_deal_amount
            FROM apartment_trade
            WHERE lawd_cd = ?
              AND deal_ym = ?
              AND apartment_name = ?
              AND ROUND(exclusive_area, 1) = ?
              AND deal_amount IS NOT NULL
            """,
            (lawd_cd, prev_deal_ym, row["apartment_name"], row["area"]),
        ).fetchone()
        prev_avg = int(prev["avg_deal_amount"]) if prev and prev["avg_deal_amount"] else None
        avg_amount = int(row["avg_deal_amount"])
        stats.append(
            ComplexStat(
                apartment_name=row["apartment_name"],
                dong=row["dong"],
                exclusive_area_group=area_group(row["area"]),
                trade_count=int(row["trade_count"]),
                avg_deal_amount=avg_amount,
                min_deal_amount=int(row["min_deal_amount"]),
                max_deal_amount=int(row["max_deal_amount"]),
                avg_price_per_pyeong=int(row["avg_price_per_pyeong"]) if row["avg_price_per_pyeong"] else None,
                prev_avg_deal_amount=prev_avg,
                price_change_rate=change_rate(avg_amount, prev_avg),
            )
        )
    return stats
