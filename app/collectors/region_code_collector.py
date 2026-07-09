from __future__ import annotations

import json
import math
from urllib.parse import urlencode
from urllib.request import urlopen

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

from app.db.models import RegionCode


DEFAULT_ENDPOINT = "https://apis.data.go.kr/1741000/StanReginCd/getStanReginCdList"


class RegionCodeCollector:
    def __init__(
        self,
        api_key: str,
        endpoint: str = DEFAULT_ENDPOINT,
        timeout: int = 20,
        num_rows: int = 1000,
    ) -> None:
        if not api_key:
            raise ValueError("PUBLIC_DATA_API_KEY is required for region code lookup.")
        self.api_key = api_key
        self.endpoint = endpoint
        self.timeout = timeout
        self.num_rows = num_rows

    def search(self, keyword: str) -> list[RegionCode]:
        page_no = 1
        total_count: int | None = None
        regions: list[RegionCode] = []

        while True:
            payload = self._request_page(keyword, page_no)
            page_items, page_total = parse_region_code_json(payload)
            regions.extend(page_items)
            total_count = page_total if page_total is not None else total_count

            if total_count is None:
                break
            max_page = max(1, math.ceil(total_count / self.num_rows))
            if page_no >= max_page:
                break
            page_no += 1

        return regions

    def _request_page(self, keyword: str, page_no: int) -> dict[str, object]:
        params = {
            "serviceKey": self.api_key,
            "type": "json",
            "pageNo": page_no,
            "numOfRows": self.num_rows,
            "flag": "Y",
            "locatadd_nm": keyword,
        }
        if requests is not None:
            response = requests.get(self.endpoint, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        url = f"{self.endpoint}?{urlencode(params)}"
        with urlopen(url, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))


def parse_region_code_json(payload: dict[str, object]) -> tuple[list[RegionCode], int | None]:
    rows = payload.get("StanReginCd")
    if not isinstance(rows, list) or len(rows) < 2:
        return [], None

    head = rows[0].get("head", []) if isinstance(rows[0], dict) else []
    total_count = _find_total_count(head)
    raw_rows = rows[1].get("row", []) if isinstance(rows[1], dict) else []
    if isinstance(raw_rows, dict):
        raw_rows = [raw_rows]

    parsed: list[RegionCode] = []
    for row in raw_rows:
        if not isinstance(row, dict):
            continue
        region_cd = str(row.get("region_cd", ""))
        sido_cd = str(row.get("sido_cd", ""))
        sgg_cd = str(row.get("sgg_cd", ""))
        if not region_cd or not sido_cd or not sgg_cd or sgg_cd == "000":
            continue
        address = str(row.get("locatadd_nm", "")).strip()
        parts = address.split()
        parsed.append(
            RegionCode(
                lawd_cd=region_cd[:5],
                sido=parts[0] if parts else "",
                sigungu=" ".join(parts[1:3]) if len(parts) > 1 else "",
                raw_json=json.dumps(row, ensure_ascii=False),
            )
        )
    return parsed, total_count


def _find_total_count(head: object) -> int | None:
    if not isinstance(head, list):
        return None
    for item in head:
        if isinstance(item, dict) and "totalCount" in item:
            try:
                return int(item["totalCount"])
            except (TypeError, ValueError):
                return None
    return None
