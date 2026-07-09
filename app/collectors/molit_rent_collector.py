from __future__ import annotations

import json
import math
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from urllib.request import urlopen

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

from app.collectors.public_data_utils import clean_text, parse_amount, to_float, to_int
from app.db.models import ApartmentRent


DEFAULT_ENDPOINT = "https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent"


class MolitRentCollector:
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

    def fetch_month(self, lawd_cd: str, deal_ym: str) -> list[ApartmentRent]:
        page_no = 1
        total_count: int | None = None
        rents: list[ApartmentRent] = []

        while True:
            xml_text = self._request_page(lawd_cd, deal_ym, page_no)
            page_items, page_total = parse_rent_xml(xml_text, lawd_cd, deal_ym)
            rents.extend(page_items)

            total_count = page_total if page_total is not None else total_count
            if total_count is None:
                if not page_items:
                    break
            else:
                max_page = max(1, math.ceil(total_count / self.num_rows))
                if page_no >= max_page:
                    break

            page_no += 1

        return rents

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


def parse_rent_xml(xml_text: str, lawd_cd: str, deal_ym: str) -> tuple[list[ApartmentRent], int | None]:
    root = ET.fromstring(xml_text)
    result_code = _text(root, ".//resultCode")
    if result_code and result_code not in {"00", "000"}:
        result_message = _text(root, ".//resultMsg") or "unknown API error"
        raise RuntimeError(f"MOLIT rent API failed: {result_code} {result_message}")

    total_count = to_int(_text(root, ".//totalCount"))
    rents = [_item_to_rent(item, lawd_cd, deal_ym) for item in root.findall(".//item")]
    return rents, total_count


def _item_to_rent(item: ET.Element, lawd_cd: str, fallback_deal_ym: str) -> ApartmentRent:
    data = {child.tag: (child.text or "").strip() for child in item}
    year = data.get("dealYear")
    month = data.get("dealMonth")
    day = data.get("dealDay")
    deal_ym = f"{year}{int(month):02d}" if year and month and month.isdigit() else fallback_deal_ym

    return ApartmentRent(
        lawd_cd=lawd_cd,
        deal_ym=deal_ym,
        deal_day=to_int(day),
        dong=clean_text(data.get("umdNm") or data.get("dong")),
        apartment_name=clean_text(data.get("aptNm") or data.get("apartmentName")) or "unknown",
        exclusive_area=to_float(data.get("excluUseAr")),
        deposit_amount=parse_amount(data.get("deposit") or data.get("depositAmount")),
        monthly_rent=parse_amount(data.get("monthlyRent")),
        floor=to_int(data.get("floor")),
        build_year=to_int(data.get("buildYear")),
        contract_type=clean_text(data.get("contractType")),
        raw_json=json.dumps(data, ensure_ascii=False),
    )


def _text(root: ET.Element, path: str) -> str | None:
    node = root.find(path)
    if node is None or node.text is None:
        return None
    return node.text.strip()
