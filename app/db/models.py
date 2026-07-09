from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApartmentTrade:
    lawd_cd: str
    deal_ym: str
    deal_day: int | None
    dong: str | None
    apartment_name: str
    exclusive_area: float | None
    deal_amount: int | None
    floor: int | None
    build_year: int | None
    raw_json: str


@dataclass(frozen=True)
class ApartmentRent:
    lawd_cd: str
    deal_ym: str
    deal_day: int | None
    dong: str | None
    apartment_name: str
    exclusive_area: float | None
    deposit_amount: int | None
    monthly_rent: int | None
    floor: int | None
    build_year: int | None
    contract_type: str | None
    raw_json: str


@dataclass(frozen=True)
class RegionCode:
    lawd_cd: str
    sido: str
    sigungu: str
    raw_json: str


@dataclass(frozen=True)
class RebStatistic:
    source: str
    statbl_id: str
    cycle: str | None
    period: str | None
    region_name: str | None
    item_name: str | None
    value: float | None
    raw_json: str


@dataclass(frozen=True)
class ExchangeRate:
    source: str
    search_date: str | None
    currency_unit: str
    currency_name: str | None
    deal_bas_r: float | None
    ttb: float | None
    tts: float | None
    raw_json: str


@dataclass(frozen=True)
class EcosStatistic:
    stat_code: str
    cycle: str | None
    period: str | None
    item_code1: str | None
    item_name1: str | None
    item_code2: str | None
    item_name2: str | None
    value: float | None
    raw_json: str


@dataclass(frozen=True)
class StockQuote:
    source: str
    market: str
    symbol: str
    name: str | None
    trade_date: str | None
    price: float | None
    change: float | None
    change_rate: float | None
    raw_json: str


@dataclass(frozen=True)
class SearchTrendPoint:
    source: str
    title: str
    keyword_group: str
    period: str
    ratio: float | None
    raw_json: str


@dataclass(frozen=True)
class CommercialStore:
    business_id: str
    business_name: str
    category_large: str | None
    category_middle: str | None
    category_small: str | None
    longitude: float | None
    latitude: float | None
    raw_json: str
