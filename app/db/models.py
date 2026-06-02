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
