from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import requests


KEYWORD_ENDPOINT = "https://dapi.kakao.com/v2/local/search/keyword.json"
CATEGORY_ENDPOINT = "https://dapi.kakao.com/v2/local/search/category.json"

CATEGORY_CODES = {
    "large_mart": "MT1",
    "convenience_store": "CS2",
    "school": "SC4",
    "academy": "AC5",
    "subway": "SW8",
    "restaurant": "FD6",
    "cafe": "CE7",
    "hospital": "HP8",
    "pharmacy": "PM9",
}


@dataclass(frozen=True)
class LocalPlace:
    place_id: str
    name: str
    category_name: str | None
    address: str | None
    road_address: str | None
    longitude: float
    latitude: float
    distance_m: int | None
    place_url: str | None


@dataclass(frozen=True)
class PlaceSearchResult:
    total_count: int
    places: list[LocalPlace]


class KakaoLocalCollector:
    def __init__(
        self,
        rest_api_key: str,
        timeout: int = 20,
        http_get: Callable[..., Any] | None = None,
    ) -> None:
        if not rest_api_key:
            raise ValueError("KAKAO_REST_API_KEY is required for local place collection.")
        self.rest_api_key = rest_api_key
        self.timeout = timeout
        self.http_get = http_get or requests.get

    def find_apartment(self, apartment_name: str, region_name: str = "") -> LocalPlace:
        query = " ".join(part for part in (region_name.strip(), apartment_name.strip()) if part)
        result = self.search_keyword(query, size=15)
        if not result.places:
            raise LookupError(f"Kakao Local did not find an apartment for: {query}")

        normalized = _normalize_name(apartment_name)
        exact = [place for place in result.places if normalized in _normalize_name(place.name)]
        return exact[0] if exact else result.places[0]

    def search_category(
        self,
        category_code: str,
        longitude: float,
        latitude: float,
        radius_m: int,
    ) -> PlaceSearchResult:
        return self._search(
            CATEGORY_ENDPOINT,
            {
                "category_group_code": category_code,
                "x": longitude,
                "y": latitude,
                "radius": radius_m,
                "sort": "distance",
            },
            size=15,
        )

    def search_keyword(
        self,
        query: str,
        longitude: float | None = None,
        latitude: float | None = None,
        radius_m: int | None = None,
        size: int = 15,
    ) -> PlaceSearchResult:
        params: dict[str, object] = {"query": query, "sort": "accuracy"}
        if longitude is not None and latitude is not None and radius_m is not None:
            params.update({"x": longitude, "y": latitude, "radius": radius_m, "sort": "distance"})
        return self._search(KEYWORD_ENDPOINT, params, size=min(max(size, 1), 15))

    def _search(self, endpoint: str, params: dict[str, object], size: int) -> PlaceSearchResult:
        places: list[LocalPlace] = []
        total_count = 0
        page = 1

        while page <= 3:
            payload = self._request_json(endpoint, {**params, "page": page, "size": size})
            meta = payload.get("meta") if isinstance(payload, dict) else None
            documents = payload.get("documents") if isinstance(payload, dict) else None
            if not isinstance(meta, dict) or not isinstance(documents, list):
                raise RuntimeError(f"Unexpected Kakao Local response: {payload}")

            total_count = _to_int(meta.get("total_count")) or total_count
            places.extend(_parse_place(item) for item in documents if isinstance(item, dict))
            if bool(meta.get("is_end")) or not documents:
                break
            page += 1

        unique = {place.place_id or f"{place.name}:{place.longitude}:{place.latitude}": place for place in places}
        return PlaceSearchResult(total_count=total_count, places=list(unique.values()))

    def _request_json(self, endpoint: str, params: dict[str, object]) -> dict[str, object]:
        response = self.http_get(
            endpoint,
            params=params,
            headers={"Authorization": f"KakaoAK {self.rest_api_key}"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError(f"Unexpected Kakao Local response: {payload}")
        return payload


def _parse_place(item: dict[str, object]) -> LocalPlace:
    return LocalPlace(
        place_id=str(item.get("id") or ""),
        name=str(item.get("place_name") or "").strip(),
        category_name=_clean_text(item.get("category_name")),
        address=_clean_text(item.get("address_name")),
        road_address=_clean_text(item.get("road_address_name")),
        longitude=float(item.get("x") or 0),
        latitude=float(item.get("y") or 0),
        distance_m=_to_int(item.get("distance")),
        place_url=_clean_text(item.get("place_url")),
    )


def _normalize_name(value: str) -> str:
    return "".join(char for char in value.lower() if char.isalnum())


def _clean_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _to_int(value: object) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None
