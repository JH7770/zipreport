from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from app.config import REGIONS
from app.db.models import (
    ApartmentRent,
    ApartmentTrade,
    CommercialStore,
    EcosStatistic,
    ExchangeRate,
    RebStatistic,
    RegionCode,
    SearchTrendPoint,
    StockQuote,
)


SCHEMA = """
CREATE TABLE IF NOT EXISTS region (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sido TEXT NOT NULL,
    sigungu TEXT NOT NULL,
    lawd_cd TEXT NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS apartment_trade (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lawd_cd TEXT NOT NULL,
    deal_ym TEXT NOT NULL,
    deal_day INTEGER,
    dong TEXT,
    apartment_name TEXT NOT NULL,
    exclusive_area REAL,
    deal_amount INTEGER,
    floor INTEGER,
    build_year INTEGER,
    raw_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (
        lawd_cd,
        deal_ym,
        deal_day,
        apartment_name,
        exclusive_area,
        floor,
        deal_amount
    )
);

CREATE TABLE IF NOT EXISTS apartment_rent (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lawd_cd TEXT NOT NULL,
    deal_ym TEXT NOT NULL,
    deal_day INTEGER,
    dong TEXT,
    apartment_name TEXT NOT NULL,
    exclusive_area REAL,
    deposit_amount INTEGER,
    monthly_rent INTEGER,
    floor INTEGER,
    build_year INTEGER,
    contract_type TEXT,
    raw_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (
        lawd_cd,
        deal_ym,
        deal_day,
        apartment_name,
        exclusive_area,
        floor,
        deposit_amount,
        monthly_rent
    )
);

CREATE TABLE IF NOT EXISTS reb_statistic (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    statbl_id TEXT NOT NULL,
    cycle TEXT,
    period TEXT,
    region_name TEXT,
    item_name TEXT,
    value REAL,
    raw_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS exchange_rate (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    search_date TEXT,
    currency_unit TEXT NOT NULL,
    currency_name TEXT,
    deal_bas_r REAL,
    ttb REAL,
    tts REAL,
    raw_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ecos_statistic (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_code TEXT NOT NULL,
    cycle TEXT,
    period TEXT,
    item_code1 TEXT,
    item_name1 TEXT,
    item_code2 TEXT,
    item_name2 TEXT,
    value REAL,
    raw_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stock_quote (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    market TEXT NOT NULL,
    symbol TEXT NOT NULL,
    name TEXT,
    trade_date TEXT,
    price REAL,
    change REAL,
    change_rate REAL,
    raw_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS search_trend_point (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    keyword_group TEXT NOT NULL,
    period TEXT NOT NULL,
    ratio REAL,
    raw_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS commercial_store_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    apartment_name TEXT NOT NULL,
    radius_m INTEGER NOT NULL,
    snapshot_date TEXT NOT NULL,
    business_id TEXT NOT NULL,
    business_name TEXT NOT NULL,
    category_large TEXT,
    category_middle TEXT,
    category_small TEXT,
    longitude REAL,
    latitude REAL,
    raw_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (apartment_name, radius_m, snapshot_date, business_id)
);

CREATE TABLE IF NOT EXISTS apartment_monthly_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lawd_cd TEXT NOT NULL,
    deal_ym TEXT NOT NULL,
    apartment_name TEXT,
    dong TEXT,
    exclusive_area_group TEXT,
    trade_count INTEGER,
    avg_deal_amount INTEGER,
    min_deal_amount INTEGER,
    max_deal_amount INTEGER,
    avg_price_per_pyeong INTEGER,
    prev_avg_deal_amount INTEGER,
    price_change_rate REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wordpress_post (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_type TEXT NOT NULL,
    region TEXT,
    deal_ym TEXT,
    title TEXT NOT NULL,
    wordpress_post_id INTEGER,
    status TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def initialize(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    for lawd_cd, region in REGIONS.items():
        conn.execute(
            """
            INSERT OR IGNORE INTO region (sido, sigungu, lawd_cd)
            VALUES (?, ?, ?)
            """,
            (region["sido"], region["sigungu"], lawd_cd),
        )
    conn.commit()


def insert_trades(conn: sqlite3.Connection, trades: Iterable[ApartmentTrade]) -> int:
    inserted = 0
    for trade in trades:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO apartment_trade (
                lawd_cd, deal_ym, deal_day, dong, apartment_name,
                exclusive_area, deal_amount, floor, build_year, raw_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trade.lawd_cd,
                trade.deal_ym,
                trade.deal_day,
                trade.dong,
                trade.apartment_name,
                trade.exclusive_area,
                trade.deal_amount,
                trade.floor,
                trade.build_year,
                trade.raw_json,
            ),
        )
        inserted += cursor.rowcount
    conn.commit()
    return inserted


def upsert_region_codes(conn: sqlite3.Connection, regions: Iterable[RegionCode]) -> int:
    changed = 0
    for region in regions:
        cursor = conn.execute(
            """
            INSERT INTO region (sido, sigungu, lawd_cd)
            VALUES (?, ?, ?)
            ON CONFLICT(lawd_cd) DO UPDATE SET
                sido = excluded.sido,
                sigungu = excluded.sigungu
            """,
            (region.sido, region.sigungu, region.lawd_cd),
        )
        changed += cursor.rowcount
    conn.commit()
    return changed


def insert_rents(conn: sqlite3.Connection, rents: Iterable[ApartmentRent]) -> int:
    inserted = 0
    for rent in rents:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO apartment_rent (
                lawd_cd, deal_ym, deal_day, dong, apartment_name,
                exclusive_area, deposit_amount, monthly_rent, floor,
                build_year, contract_type, raw_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rent.lawd_cd,
                rent.deal_ym,
                rent.deal_day,
                rent.dong,
                rent.apartment_name,
                rent.exclusive_area,
                rent.deposit_amount,
                rent.monthly_rent,
                rent.floor,
                rent.build_year,
                rent.contract_type,
                rent.raw_json,
            ),
        )
        inserted += cursor.rowcount
    conn.commit()
    return inserted


def insert_reb_statistics(conn: sqlite3.Connection, rows: Iterable[RebStatistic]) -> int:
    inserted = 0
    for row in rows:
        cursor = conn.execute(
            """
            INSERT INTO reb_statistic (
                source, statbl_id, cycle, period, region_name, item_name, value, raw_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row.source,
                row.statbl_id,
                row.cycle,
                row.period,
                row.region_name,
                row.item_name,
                row.value,
                row.raw_json,
            ),
        )
        inserted += cursor.rowcount
    conn.commit()
    return inserted


def insert_exchange_rates(conn: sqlite3.Connection, rows: Iterable[ExchangeRate]) -> int:
    inserted = 0
    for row in rows:
        cursor = conn.execute(
            """
            INSERT INTO exchange_rate (
                source, search_date, currency_unit, currency_name,
                deal_bas_r, ttb, tts, raw_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row.source,
                row.search_date,
                row.currency_unit,
                row.currency_name,
                row.deal_bas_r,
                row.ttb,
                row.tts,
                row.raw_json,
            ),
        )
        inserted += cursor.rowcount
    conn.commit()
    return inserted


def insert_ecos_statistics(conn: sqlite3.Connection, rows: Iterable[EcosStatistic]) -> int:
    inserted = 0
    for row in rows:
        cursor = conn.execute(
            """
            INSERT INTO ecos_statistic (
                stat_code, cycle, period, item_code1, item_name1,
                item_code2, item_name2, value, raw_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row.stat_code,
                row.cycle,
                row.period,
                row.item_code1,
                row.item_name1,
                row.item_code2,
                row.item_name2,
                row.value,
                row.raw_json,
            ),
        )
        inserted += cursor.rowcount
    conn.commit()
    return inserted


def insert_stock_quotes(conn: sqlite3.Connection, rows: Iterable[StockQuote]) -> int:
    inserted = 0
    for row in rows:
        cursor = conn.execute(
            """
            INSERT INTO stock_quote (
                source, market, symbol, name, trade_date,
                price, change, change_rate, raw_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row.source,
                row.market,
                row.symbol,
                row.name,
                row.trade_date,
                row.price,
                row.change,
                row.change_rate,
                row.raw_json,
            ),
        )
        inserted += cursor.rowcount
    conn.commit()
    return inserted


def insert_search_trend_points(conn: sqlite3.Connection, rows: Iterable[SearchTrendPoint]) -> int:
    inserted = 0
    for row in rows:
        cursor = conn.execute(
            """
            INSERT INTO search_trend_point (
                source, title, keyword_group, period, ratio, raw_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                row.source,
                row.title,
                row.keyword_group,
                row.period,
                row.ratio,
                row.raw_json,
            ),
        )
        inserted += cursor.rowcount
    conn.commit()
    return inserted


def save_commercial_store_snapshot(
    conn: sqlite3.Connection,
    apartment_name: str,
    radius_m: int,
    snapshot_date: str,
    stores: Iterable[CommercialStore],
) -> int:
    inserted = 0
    for store in stores:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO commercial_store_snapshot (
                apartment_name, radius_m, snapshot_date, business_id,
                business_name, category_large, category_middle, category_small,
                longitude, latitude, raw_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                apartment_name,
                radius_m,
                snapshot_date,
                store.business_id,
                store.business_name,
                store.category_large,
                store.category_middle,
                store.category_small,
                store.longitude,
                store.latitude,
                store.raw_json,
            ),
        )
        inserted += cursor.rowcount
    conn.commit()
    return inserted


def save_wordpress_post(
    conn: sqlite3.Connection,
    post_type: str,
    region: str,
    deal_ym: str,
    title: str,
    wordpress_post_id: int | None,
    status: str,
) -> None:
    conn.execute(
        """
        INSERT INTO wordpress_post (
            post_type, region, deal_ym, title, wordpress_post_id, status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (post_type, region, deal_ym, title, wordpress_post_id, status),
    )
    conn.commit()
