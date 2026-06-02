from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from app.config import REGIONS
from app.db.models import ApartmentTrade


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
