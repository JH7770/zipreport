from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

from app.collectors.public_data_utils import clean_text, to_float
from app.db.models import StockQuote


DEFAULT_BASE_URL = "https://openapi.koreainvestment.com:9443"
PRICE_PATH = "/uapi/domestic-stock/v1/quotations/inquire-price"
TOKEN_PATH = "/oauth2/tokenP"


class KisQuoteCollector:
    def __init__(
        self,
        app_key: str,
        app_secret: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = 20,
    ) -> None:
        if not app_key or not app_secret:
            raise ValueError("KIS_APP_KEY and KIS_APP_SECRET are required for live collection.")
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def fetch_domestic_price(self, symbol: str, market: str = "J") -> StockQuote:
        token = self.issue_access_token()
        headers = {
            "authorization": f"Bearer {token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "FHKST01010100",
            "custtype": "P",
        }
        params = {"FID_COND_MRKT_DIV_CODE": market, "FID_INPUT_ISCD": symbol}
        payload = self._get_json(f"{self.base_url}{PRICE_PATH}", headers=headers, params=params)
        return parse_kis_domestic_price(payload, symbol=symbol, market=market)

    def issue_access_token(self) -> str:
        payload = {"grant_type": "client_credentials", "appkey": self.app_key, "appsecret": self.app_secret}
        data = self._post_json(f"{self.base_url}{TOKEN_PATH}", payload)
        token = clean_text(data.get("access_token"))
        if not token:
            raise RuntimeError(f"KIS token response did not include access_token: {data}")
        return token

    def _post_json(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        if requests is not None:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        body = json.dumps(payload).encode("utf-8")
        request = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def _get_json(self, url: str, headers: dict[str, str], params: dict[str, str]) -> dict[str, Any]:
        if requests is not None:
            response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        request = Request(f"{url}?{urlencode(params)}", headers=headers, method="GET")
        with urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))


def parse_kis_domestic_price(payload: dict[str, Any], symbol: str, market: str = "J") -> StockQuote:
    if clean_text(payload.get("rt_cd")) not in {None, "0"}:
        raise RuntimeError(f"KIS quote API failed: {payload.get('msg_cd')} {payload.get('msg1')}")
    output = payload.get("output") if isinstance(payload.get("output"), dict) else {}
    return StockQuote(
        source="KIS",
        market=market,
        symbol=symbol,
        name=clean_text(output.get("hts_kor_isnm")),
        trade_date=clean_text(output.get("stck_bsop_date")),
        price=to_float(output.get("stck_prpr")),
        change=to_float(output.get("prdy_vrss")),
        change_rate=to_float(output.get("prdy_ctrt")),
        raw_json=json.dumps(output, ensure_ascii=False),
    )
