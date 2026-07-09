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
from app.db.models import ExchangeRate


DEFAULT_ENDPOINT = "https://www.koreaexim.go.kr/site/program/financial/exchangeJSON"


class EximExchangeCollector:
    def __init__(self, api_key: str, endpoint: str = DEFAULT_ENDPOINT, timeout: int = 20) -> None:
        if not api_key:
            raise ValueError("EXIM_API_KEY is required for live collection.")
        self.api_key = api_key
        self.endpoint = endpoint
        self.timeout = timeout

    def fetch_daily(self, search_date: str | None = None, data_type: str = "AP01") -> list[ExchangeRate]:
        params = {"authkey": self.api_key, "data": data_type}
        if search_date:
            params["searchdate"] = search_date
        payload = self._request(params)
        return parse_exchange_rates(payload, search_date)

    def _request(self, params: dict[str, str]) -> list[dict[str, Any]]:
        if requests is not None:
            response = requests.get(self.endpoint, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        url = f"{self.endpoint}?{urlencode(params)}"
        with urlopen(url, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))


def parse_exchange_rates(payload: list[dict[str, Any]], search_date: str | None = None) -> list[ExchangeRate]:
    rows: list[ExchangeRate] = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        result = clean_text(row.get("result") or row.get("RESULT"))
        if result and result != "1":
            raise RuntimeError(f"EXIM exchange API failed with result={result}")
        currency_unit = clean_text(row.get("cur_unit") or row.get("CUR_UNIT"))
        if not currency_unit:
            continue
        rows.append(
            ExchangeRate(
                source="EXIM",
                search_date=search_date,
                currency_unit=currency_unit,
                currency_name=clean_text(row.get("cur_nm") or row.get("CUR_NM")),
                deal_bas_r=to_float(row.get("deal_bas_r") or row.get("DEAL_BAS_R")),
                ttb=to_float(row.get("ttb") or row.get("TTB")),
                tts=to_float(row.get("tts") or row.get("TTS")),
                raw_json=json.dumps(row, ensure_ascii=False),
            )
        )
    return rows
