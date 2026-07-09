from __future__ import annotations

import sqlite3
from datetime import date, timedelta

from app.analyzers.apartment_living_analyzer import (
    ApartmentLivingReport,
    analyze_apartment_trades,
    analyze_commercial_snapshot,
    build_facility_summary,
    build_facility_summary_from_stores,
    build_school_summary,
    build_transit_summary,
    calculate_scores,
)
from app.collectors.commercial_district_collector import CommercialDistrictCollector
from app.collectors.kakao_local_collector import CATEGORY_CODES, KakaoLocalCollector, LocalPlace, PlaceSearchResult
from app.collectors.neis_school_collector import NeisSchoolCollector, SchoolMetadata
from app.collectors.seoul_subway_collector import SeoulSubwayCollector, SubwayUsage
from app.config import REGIONS, Settings


def build_apartment_living_report(
    conn: sqlite3.Connection,
    settings: Settings,
    apartment_name: str,
    lawd_cd: str,
    deal_ym: str,
    radius_m: int = 1000,
    snapshot_date: str | None = None,
    transit_date: str | None = None,
    longitude: float | None = None,
    latitude: float | None = None,
    address: str | None = None,
    station_name: str | None = None,
    station_distance_m: int | None = None,
    school_names: list[str] | None = None,
) -> ApartmentLivingReport:
    snapshot_date = snapshot_date or date.today().isoformat()
    transit_date = transit_date or (date.today() - timedelta(days=4)).strftime("%Y%m%d")
    warnings: list[str] = []
    region = REGIONS.get(lawd_cd, {"sido": "", "sigungu": lawd_cd})
    region_name = f"{region['sido']} {region['sigungu']}".strip()

    results: dict[str, PlaceSearchResult] = {}
    apartment_longitude = longitude
    apartment_latitude = latitude
    apartment_address = address
    if settings.kakao_rest_api_key:
        try:
            kakao = KakaoLocalCollector(settings.kakao_rest_api_key)
            apartment = kakao.find_apartment(apartment_name, region_name)
            apartment_longitude = apartment.longitude
            apartment_latitude = apartment.latitude
            apartment_address = apartment.road_address or apartment.address or apartment_address
            for key, category_code in CATEGORY_CODES.items():
                results[key] = kakao.search_category(
                    category_code,
                    apartment_longitude,
                    apartment_latitude,
                    radius_m,
                )
            for key, query in {"park": "공원", "starbucks": "스타벅스", "chicken": "치킨"}.items():
                results[key] = kakao.search_keyword(
                    query,
                    apartment_longitude,
                    apartment_latitude,
                    radius_m,
                )
        except Exception:
            warnings.append("카카오 로컬 서비스가 비활성화되어 상가업소 데이터로 대체했습니다.")

    if apartment_longitude is None or apartment_latitude is None:
        raise ValueError("Apartment longitude and latitude are required when Kakao Local is unavailable.")

    school_result = results.get("school")
    if school_names and not school_result:
        school_result = PlaceSearchResult(
            total_count=len(school_names),
            places=[
                LocalPlace(
                    place_id=f"manual-school-{index}",
                    name=name,
                    category_name="학교",
                    address=None,
                    road_address=None,
                    longitude=apartment_longitude,
                    latitude=apartment_latitude,
                    distance_m=None,
                    place_url=None,
                )
                for index, name in enumerate(school_names, 1)
            ],
        )
    school_metadata = _collect_school_metadata(settings, school_result, warnings)
    schools = build_school_summary(school_result, school_metadata)

    subway_result = results.get("subway")
    if station_name and not subway_result:
        subway_result = PlaceSearchResult(
            total_count=1,
            places=[
                LocalPlace(
                    place_id="manual-station",
                    name=station_name,
                    category_name="지하철역",
                    address=None,
                    road_address=None,
                    longitude=apartment_longitude,
                    latitude=apartment_latitude,
                    distance_m=station_distance_m,
                    place_url=None,
                )
            ],
        )
    subway_usage = _collect_subway_usage(
        settings,
        region_name,
        subway_result,
        transit_date,
        warnings,
    )
    transit = build_transit_summary(subway_result, subway_usage)
    facilities = build_facility_summary(radius_m, results)
    trade = analyze_apartment_trades(conn, lawd_cd, apartment_name, deal_ym)

    stores = None
    if settings.public_data_api_key:
        try:
            stores = CommercialDistrictCollector(
                settings.public_data_api_key,
                settings.commercial_district_endpoint,
            ).fetch_radius(apartment_longitude, apartment_latitude, radius_m)
        except Exception as exc:
            warnings.append(f"상가업소 API 조회 실패: {exc}")
    else:
        warnings.append("PUBLIC_DATA_API_KEY가 없어 상가업소 스냅샷을 생략했습니다.")

    commercial = analyze_commercial_snapshot(
        conn,
        trade.apartment_name,
        radius_m,
        snapshot_date,
        stores,
    )
    if not results and stores is not None:
        facilities = build_facility_summary_from_stores(radius_m, stores)
        warnings.append("생활시설 수는 카카오 대신 상가업소 업종 분류에서 집계했습니다.")
    scores, ratings = calculate_scores(trade, facilities, schools, transit, commercial)

    return ApartmentLivingReport(
        apartment_name=trade.apartment_name,
        address=apartment_address,
        longitude=apartment_longitude,
        latitude=apartment_latitude,
        radius_m=radius_m,
        snapshot_date=snapshot_date,
        trade=trade,
        facilities=facilities,
        schools=schools,
        transit=transit,
        commercial=commercial,
        scores=scores,
        ratings=ratings,
        warnings=warnings,
    )


def _collect_school_metadata(
    settings: Settings,
    result: PlaceSearchResult | None,
    warnings: list[str],
) -> dict[str, SchoolMetadata]:
    if not settings.neis_api_key or result is None:
        if not settings.neis_api_key:
            warnings.append("NEIS_API_KEY가 없어 학교 유형은 학교명으로 분류했습니다.")
        return {}
    collector = NeisSchoolCollector(settings.neis_api_key)
    metadata: dict[str, SchoolMetadata] = {}
    for place in result.places[:10]:
        try:
            school = collector.lookup_school(place.name)
            if school:
                metadata[place.name] = school
        except Exception as exc:
            warnings.append(f"나이스 학교정보 조회 실패({place.name}): {exc}")
    return metadata


def _collect_subway_usage(
    settings: Settings,
    region_name: str,
    result: PlaceSearchResult | None,
    transit_date: str,
    warnings: list[str],
) -> SubwayUsage | None:
    if result is None or not result.places:
        return None
    if "서울" not in region_name:
        warnings.append("서울 외 지역은 서울 열린데이터광장 승하차 자료를 적용하지 않았습니다.")
        return None
    if not settings.seoul_open_data_key:
        warnings.append("SEOUL_OPEN_DATA_KEY가 없어 지하철 승하차 인원을 생략했습니다.")
        return None
    try:
        return SeoulSubwayCollector(settings.seoul_open_data_key).find_station(
            transit_date,
            result.places[0].name,
        )
    except Exception as exc:
        warnings.append(f"서울 지하철 승하차 조회 실패: {exc}")
        return None
