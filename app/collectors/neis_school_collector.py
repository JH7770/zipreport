from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import requests


DEFAULT_ENDPOINT = "https://open.neis.go.kr/hub/schoolInfo"


@dataclass(frozen=True)
class SchoolMetadata:
    name: str
    school_kind: str | None
    foundation: str | None
    address: str | None
    homepage: str | None


class NeisSchoolCollector:
    def __init__(
        self,
        api_key: str,
        endpoint: str = DEFAULT_ENDPOINT,
        timeout: int = 20,
        http_get: Callable[..., Any] | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("NEIS_API_KEY is required for school metadata collection.")
        self.api_key = api_key
        self.endpoint = endpoint
        self.timeout = timeout
        self.http_get = http_get or requests.get

    def lookup_school(self, school_name: str) -> SchoolMetadata | None:
        response = self.http_get(
            self.endpoint,
            params={
                "KEY": self.api_key,
                "Type": "json",
                "pIndex": 1,
                "pSize": 20,
                "SCHUL_NM": school_name,
            },
            timeout=self.timeout,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"NEIS API failed: HTTP {response.status_code}")
        rows = parse_school_response(response.json())
        normalized = _normalize_school_name(school_name)
        for row in rows:
            if _normalize_school_name(row.name) == normalized:
                return row
        return rows[0] if rows else None


def parse_school_response(payload: object) -> list[SchoolMetadata]:
    if not isinstance(payload, dict):
        raise RuntimeError(f"Unexpected NEIS response: {payload}")
    result = payload.get("schoolInfo")
    if not isinstance(result, list):
        return []
    rows: list[dict[str, object]] = []
    for section in result:
        if isinstance(section, dict) and isinstance(section.get("row"), list):
            rows.extend(item for item in section["row"] if isinstance(item, dict))
    return [
        SchoolMetadata(
            name=str(row.get("SCHUL_NM") or "").strip(),
            school_kind=_clean_text(row.get("SCHUL_KND_SC_NM")),
            foundation=_clean_text(row.get("FOND_SC_NM")),
            address=_clean_text(row.get("ORG_RDNMA")),
            homepage=_clean_text(row.get("HMPG_ADRES")),
        )
        for row in rows
    ]


def _normalize_school_name(value: str) -> str:
    return value.replace(" ", "").strip()


def _clean_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
