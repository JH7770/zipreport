from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import requests


@dataclass(frozen=True)
class SubwayUsage:
    use_date: str
    line_name: str
    station_name: str
    ride_count: int
    alight_count: int

    @property
    def total_count(self) -> int:
        return self.ride_count + self.alight_count


class SeoulSubwayCollector:
    def __init__(
        self,
        api_key: str,
        timeout: int = 30,
        http_get: Callable[..., Any] | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("SEOUL_OPEN_DATA_KEY is required for subway usage collection.")
        self.api_key = api_key
        self.timeout = timeout
        self.http_get = http_get or requests.get

    def fetch_daily(self, use_date: str) -> list[SubwayUsage]:
        endpoint = (
            f"http://openapi.seoul.go.kr:8088/{self.api_key}/json/"
            f"CardSubwayStatsNew/1/1000/{use_date}"
        )
        try:
            response = self.http_get(endpoint, timeout=self.timeout)
        except requests.RequestException:
            raise RuntimeError("Seoul subway API connection failed.") from None
        if response.status_code >= 400:
            raise RuntimeError(f"Seoul subway API failed: HTTP {response.status_code}")
        return parse_subway_response(response.json())

    def find_station(self, use_date: str, station_name: str) -> SubwayUsage | None:
        target = normalize_station_name(station_name)
        matches = [row for row in self.fetch_daily(use_date) if normalize_station_name(row.station_name) == target]
        if not matches:
            return None
        return SubwayUsage(
            use_date=use_date,
            line_name=", ".join(sorted({row.line_name for row in matches})),
            station_name=station_name,
            ride_count=sum(row.ride_count for row in matches),
            alight_count=sum(row.alight_count for row in matches),
        )


def parse_subway_response(payload: object) -> list[SubwayUsage]:
    if not isinstance(payload, dict):
        raise RuntimeError(f"Unexpected Seoul subway response: {payload}")
    service = payload.get("CardSubwayStatsNew")
    if not isinstance(service, dict):
        error = payload.get("RESULT")
        raise RuntimeError(f"Seoul subway API failed: {error or payload}")
    rows = service.get("row") or []
    if not isinstance(rows, list):
        return []
    return [
        SubwayUsage(
            use_date=str(row.get("USE_YMD") or row.get("USE_DT") or ""),
            line_name=str(row.get("SBWY_ROUT_LN_NM") or row.get("LINE_NUM") or "").strip(),
            station_name=str(row.get("SBWY_STNS_NM") or row.get("SUB_STA_NM") or "").strip(),
            ride_count=_to_int(row.get("GTON_TNOPE") or row.get("RIDE_PASGR_NUM")),
            alight_count=_to_int(row.get("GTOFF_TNOPE") or row.get("ALIGHT_PASGR_NUM")),
        )
        for row in rows
        if isinstance(row, dict)
    ]


def normalize_station_name(value: str) -> str:
    return value.replace("역", "").split("(", 1)[0].replace(" ", "").strip()


def _to_int(value: object) -> int:
    try:
        return int(float(str(value).replace(",", "")))
    except (TypeError, ValueError):
        return 0
