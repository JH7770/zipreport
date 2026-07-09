from __future__ import annotations

import json
from typing import Any
from urllib.request import Request, urlopen

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

from app.collectors.public_data_utils import clean_text, to_float
from app.db.models import SearchTrendPoint


DEFAULT_ENDPOINT = "https://openapi.naver.com/v1/datalab/search"


class NaverDatalabCollector:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        endpoint: str = DEFAULT_ENDPOINT,
        timeout: int = 20,
    ) -> None:
        if not client_id or not client_secret:
            raise ValueError("NAVER_CLIENT_ID and NAVER_CLIENT_SECRET are required for live collection.")
        self.client_id = client_id
        self.client_secret = client_secret
        self.endpoint = endpoint
        self.timeout = timeout

    def fetch_search_trends(
        self,
        start_date: str,
        end_date: str,
        keyword_groups: list[dict[str, Any]],
        time_unit: str = "date",
        device: str | None = None,
        gender: str | None = None,
        ages: list[str] | None = None,
    ) -> list[SearchTrendPoint]:
        payload: dict[str, Any] = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": time_unit,
            "keywordGroups": keyword_groups,
        }
        if device:
            payload["device"] = device
        if gender:
            payload["gender"] = gender
        if ages:
            payload["ages"] = ages
        data = self._request(payload)
        return parse_search_trends(data)

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }
        if requests is not None:
            response = requests.post(self.endpoint, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        body = json.dumps(payload).encode("utf-8")
        request = Request(self.endpoint, data=body, headers=headers, method="POST")
        with urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))


def parse_search_trends(payload: dict[str, Any]) -> list[SearchTrendPoint]:
    rows: list[SearchTrendPoint] = []
    for group in payload.get("results", []):
        if not isinstance(group, dict):
            continue
        title = clean_text(group.get("title")) or ""
        keywords = group.get("keywords", [])
        keyword_group = ",".join(str(keyword) for keyword in keywords) if isinstance(keywords, list) else str(keywords)
        for item in group.get("data", []):
            if not isinstance(item, dict):
                continue
            period = clean_text(item.get("period"))
            if not period:
                continue
            rows.append(
                SearchTrendPoint(
                    source="NAVER_DATALAB",
                    title=title,
                    keyword_group=keyword_group,
                    period=period,
                    ratio=to_float(item.get("ratio")),
                    raw_json=json.dumps(item, ensure_ascii=False),
                )
            )
    return rows
