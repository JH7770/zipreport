from __future__ import annotations

import json
import math
from typing import Any, Callable

import requests

from app.collectors.public_data_utils import clean_text, to_float, to_int
from app.db.models import CommercialStore


class CommercialDistrictCollector:
    def __init__(
        self,
        api_key: str,
        endpoint: str,
        timeout: int = 30,
        num_rows: int = 1000,
        http_get: Callable[..., Any] | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("PUBLIC_DATA_API_KEY is required for commercial district collection.")
        self.api_key = api_key
        self.endpoint = endpoint
        self.timeout = timeout
        self.num_rows = num_rows
        self.http_get = http_get or requests.get

    def fetch_radius(self, longitude: float, latitude: float, radius_m: int) -> list[CommercialStore]:
        stores: list[CommercialStore] = []
        page_no = 1
        total_count: int | None = None

        while True:
            try:
                response = self.http_get(
                    self.endpoint,
                    params={
                        "serviceKey": self.api_key,
                        "cx": longitude,
                        "cy": latitude,
                        "radius": radius_m,
                        "pageNo": page_no,
                        "numOfRows": self.num_rows,
                        "type": "json",
                    },
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:
                raise RuntimeError(
                    "Commercial district API connection failed. "
                    "Check network access and the configured endpoint."
                ) from None
            if response.status_code >= 400:
                raise RuntimeError(
                    f"Commercial district API failed: HTTP {response.status_code}. "
                    "Check the service approval and COMMERCIAL_DISTRICT_ENDPOINT."
                )
            page_stores, page_total = parse_commercial_response(response.json())
            stores.extend(page_stores)
            total_count = page_total if page_total is not None else total_count

            if not page_stores:
                break
            if total_count is not None and page_no >= max(1, math.ceil(total_count / self.num_rows)):
                break
            page_no += 1

        unique = {store.business_id: store for store in stores}
        return list(unique.values())


def parse_commercial_response(payload: object) -> tuple[list[CommercialStore], int | None]:
    if not isinstance(payload, dict):
        raise RuntimeError(f"Unexpected commercial district response: {payload}")

    header = payload.get("header")
    if isinstance(header, dict):
        result_code = str(header.get("resultCode") or header.get("stdrCd") or "00")
        if result_code not in {"00", "000", "0000"}:
            raise RuntimeError(f"Commercial district API failed: {result_code} {header}")

    body = payload.get("body")
    if not isinstance(body, dict):
        response = payload.get("response")
        body = response.get("body") if isinstance(response, dict) else None
    if not isinstance(body, dict):
        raise RuntimeError(f"Unexpected commercial district response: {payload}")

    raw_items = body.get("items") or []
    if isinstance(raw_items, dict):
        raw_items = raw_items.get("item") or []
    if isinstance(raw_items, dict):
        raw_items = [raw_items]
    if not isinstance(raw_items, list):
        raw_items = []

    stores = [_parse_store(item) for item in raw_items if isinstance(item, dict)]
    return stores, to_int(body.get("totalCount"))


def _parse_store(item: dict[str, object]) -> CommercialStore:
    business_id = clean_text(item.get("bizesId") or item.get("storeId") or item.get("상가업소번호"))
    business_name = clean_text(item.get("bizesNm") or item.get("storeNm") or item.get("상호명"))
    if not business_id:
        business_id = "|".join(
            str(value or "")
            for value in (
                business_name,
                item.get("lnoAdr") or item.get("지번주소"),
                item.get("indsSclsCd") or item.get("상권업종소분류코드"),
            )
        )
    return CommercialStore(
        business_id=business_id,
        business_name=business_name or "이름 미상",
        category_large=clean_text(item.get("indsLclsNm") or item.get("상권업종대분류명")),
        category_middle=clean_text(item.get("indsMclsNm") or item.get("상권업종중분류명")),
        category_small=clean_text(item.get("indsSclsNm") or item.get("상권업종소분류명")),
        longitude=to_float(item.get("lon") or item.get("경도")),
        latitude=to_float(item.get("lat") or item.get("위도")),
        raw_json=json.dumps(item, ensure_ascii=False),
    )
