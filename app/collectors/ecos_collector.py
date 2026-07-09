from __future__ import annotations

import json
from typing import Any
from urllib.request import urlopen

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

from app.collectors.public_data_utils import clean_text, to_float
from app.db.models import EcosStatistic


DEFAULT_ENDPOINT = "https://ecos.bok.or.kr/api"


class EcosCollector:
    def __init__(
        self,
        api_key: str,
        endpoint: str = DEFAULT_ENDPOINT,
        timeout: int = 20,
        language: str = "kr",
        page_size: int = 1000,
    ) -> None:
        if not api_key:
            raise ValueError("ECOS_API_KEY is required for live collection.")
        self.api_key = api_key
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout
        self.language = language
        self.page_size = page_size

    def fetch_statistic_search(
        self,
        stat_code: str,
        cycle: str,
        start_period: str,
        end_period: str,
        item_code1: str | None = None,
        item_code2: str | None = None,
        item_code3: str | None = None,
        item_code4: str | None = None,
    ) -> list[EcosStatistic]:
        parts = [
            self.endpoint,
            "StatisticSearch",
            self.api_key,
            "json",
            self.language,
            "1",
            str(self.page_size),
            stat_code,
            cycle,
            start_period,
            end_period,
        ]
        parts.extend([code for code in [item_code1, item_code2, item_code3, item_code4] if code])
        payload = self._request("/".join(parts))
        return parse_ecos_statistics(payload, stat_code)

    def _request(self, url: str) -> dict[str, Any]:
        if requests is not None:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        with urlopen(url, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))


def parse_ecos_statistics(payload: dict[str, Any], fallback_stat_code: str = "") -> list[EcosStatistic]:
    result = payload.get("StatisticSearch")
    if not isinstance(result, dict):
        return []
    if "RESULT" in result:
        code = clean_text(result["RESULT"].get("CODE"))
        message = clean_text(result["RESULT"].get("MESSAGE"))
        if code and code not in {"INFO-000"}:
            raise RuntimeError(f"ECOS API failed: {code} {message or ''}".strip())

    raw_rows = result.get("row", [])
    if isinstance(raw_rows, dict):
        raw_rows = [raw_rows]

    rows: list[EcosStatistic] = []
    for row in raw_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            EcosStatistic(
                stat_code=clean_text(row.get("STAT_CODE")) or fallback_stat_code,
                cycle=clean_text(row.get("CYCLE")),
                period=clean_text(row.get("TIME")),
                item_code1=clean_text(row.get("ITEM_CODE1")),
                item_name1=clean_text(row.get("ITEM_NAME1")),
                item_code2=clean_text(row.get("ITEM_CODE2")),
                item_name2=clean_text(row.get("ITEM_NAME2")),
                value=to_float(row.get("DATA_VALUE")),
                raw_json=json.dumps(row, ensure_ascii=False),
            )
        )
    return rows
