from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

from app.collectors.public_data_utils import clean_text, to_float
from app.db.models import RebStatistic


DEFAULT_ENDPOINT = "https://www.reb.or.kr/r-one/openapi/SttsApiTblData.do"


class RebStatisticsCollector:
    def __init__(
        self,
        api_key: str,
        endpoint: str = DEFAULT_ENDPOINT,
        timeout: int = 20,
        page_size: int = 1000,
    ) -> None:
        self.api_key = api_key
        self.endpoint = endpoint
        self.timeout = timeout
        self.page_size = page_size

    def fetch_table(
        self,
        statbl_id: str,
        cycle: str,
        period: str,
        extra_params: dict[str, str] | None = None,
    ) -> list[RebStatistic]:
        params = {
            "KEY": self.api_key or "sample",
            "Type": "json",
            "pIndex": "1",
            "pSize": str(self.page_size),
            "STATBL_ID": statbl_id,
            "DTACYCLE_CD": cycle,
            "WRTTIME_IDTFR_ID": period,
        }
        if extra_params:
            params.update(extra_params)
        payload = self._request(params)
        return parse_reb_statistics(payload, statbl_id)

    def _request(self, params: dict[str, str]) -> dict[str, Any]:
        if requests is not None:
            response = requests.get(self.endpoint, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        url = f"{self.endpoint}?{urlencode(params)}"
        with urlopen(url, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))


def parse_reb_statistics(payload: dict[str, Any], fallback_statbl_id: str = "") -> list[RebStatistic]:
    rows = payload.get("SttsApiTblData")
    if not isinstance(rows, list) or len(rows) < 2:
        return []
    raw_rows = rows[1].get("row", []) if isinstance(rows[1], dict) else []
    if isinstance(raw_rows, dict):
        raw_rows = [raw_rows]

    parsed: list[RebStatistic] = []
    for row in raw_rows:
        if not isinstance(row, dict):
            continue
        parsed.append(
            RebStatistic(
                source="REB",
                statbl_id=clean_text(row.get("STATBL_ID")) or fallback_statbl_id,
                cycle=clean_text(row.get("DTACYCLE_CD")),
                period=clean_text(row.get("WRTTIME_IDTFR_ID")),
                region_name=clean_text(row.get("CLS_NM") or row.get("ITM_NM") or row.get("C1_NM")),
                item_name=clean_text(row.get("ITM_NM") or row.get("OBJ_NM") or row.get("C2_NM")),
                value=to_float(row.get("DTA_VAL") or row.get("DATA_VAL") or row.get("VAL")),
                raw_json=json.dumps(row, ensure_ascii=False),
            )
        )
    return parsed
