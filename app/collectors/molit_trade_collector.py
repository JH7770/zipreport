from __future__ import annotations

import json
import math
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

try:
    import requests
except ImportError:  # pragma: no cover - exercised in dependency-free environments.
    requests = None

from app.db.models import ApartmentTrade


DEFAULT_ENDPOINT = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
DETAIL_ENDPOINT = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"


class MolitTradeCollector:
    def __init__(
        self,
        api_key: str,
        endpoint: str = DEFAULT_ENDPOINT,
        timeout: int = 20,
        num_rows: int = 1000,
    ) -> None:
        if not api_key:
            raise ValueError("PUBLIC_DATA_API_KEY is required for live collection.")
        self.api_key = api_key
        self.endpoint = endpoint
        self.timeout = timeout
        self.num_rows = num_rows

    def fetch_month(self, lawd_cd: str, deal_ym: str) -> list[ApartmentTrade]:
        page_no = 1
        total_count: int | None = None
        trades: list[ApartmentTrade] = []

        while True:
            xml_text = self._request_page(lawd_cd, deal_ym, page_no)
            page_items, page_total = parse_trade_xml(xml_text, lawd_cd, deal_ym)
            trades.extend(page_items)

            total_count = page_total if page_total is not None else total_count
            if total_count is None:
                if not page_items:
                    break
            else:
                max_page = max(1, math.ceil(total_count / self.num_rows))
                if page_no >= max_page:
                    break

            page_no += 1

        return trades

    def _request_page(self, lawd_cd: str, deal_ym: str, page_no: int) -> str:
        params = {
            "serviceKey": self.api_key,
            "LAWD_CD": lawd_cd,
            "DEAL_YMD": deal_ym,
            "pageNo": page_no,
            "numOfRows": self.num_rows,
        }
        if requests is not None:
            response = requests.get(self.endpoint, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.text

        url = f"{self.endpoint}?{urlencode(params)}"
        with urlopen(url, timeout=self.timeout) as response:
            return response.read().decode("utf-8")


def parse_trade_xml(xml_text: str, lawd_cd: str, deal_ym: str) -> tuple[list[ApartmentTrade], int | None]:
    root = ET.fromstring(xml_text)
    result_code = _text(root, ".//resultCode")
    if result_code and result_code not in {"00", "000"}:
        result_message = _text(root, ".//resultMsg") or "unknown API error"
        raise RuntimeError(f"MOLIT API failed: {result_code} {result_message}")

    total_count = _to_int(_text(root, ".//totalCount"))
    items = root.findall(".//item")
    trades = [_item_to_trade(item, lawd_cd, deal_ym) for item in items]
    return trades, total_count


def _item_to_trade(item: ET.Element, lawd_cd: str, fallback_deal_ym: str) -> ApartmentTrade:
    data = {child.tag: (child.text or "").strip() for child in item}
    year = data.get("dealYear") or data.get("년")
    month = data.get("dealMonth") or data.get("월")
    day = data.get("dealDay") or data.get("일")
    deal_ym = f"{year}{int(month):02d}" if year and month and month.isdigit() else fallback_deal_ym

    amount = data.get("dealAmount") or data.get("거래금액")
    area = data.get("excluUseAr") or data.get("전용면적")
    floor = data.get("floor") or data.get("층")
    build_year = data.get("buildYear") or data.get("건축년도")
    name = data.get("aptNm") or data.get("아파트") or data.get("apartmentName") or ""
    dong = data.get("umdNm") or data.get("법정동") or data.get("dong")

    return ApartmentTrade(
        lawd_cd=lawd_cd,
        deal_ym=deal_ym,
        deal_day=_to_int(day),
        dong=_clean_text(dong),
        apartment_name=_clean_text(name) or "이름 미상",
        exclusive_area=_to_float(area),
        deal_amount=_parse_amount(amount),
        floor=_to_int(floor),
        build_year=_to_int(build_year),
        raw_json=json.dumps(data, ensure_ascii=False),
    )


def _text(root: ET.Element, path: str) -> str | None:
    node = root.find(path)
    if node is None or node.text is None:
        return None
    return node.text.strip()


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).replace(",", "").strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).replace(",", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _parse_amount(value: Any) -> int | None:
    parsed = _to_int(value)
    if parsed is None:
        return None
    return parsed * 10000
