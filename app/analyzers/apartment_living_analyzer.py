from __future__ import annotations

import sqlite3
from collections import Counter
from dataclasses import dataclass
from typing import Mapping

from app.analyzers.apartment_analyzer import PYEONG_IN_SQUARE_METERS, change_rate, previous_month
from app.collectors.kakao_local_collector import LocalPlace, PlaceSearchResult
from app.collectors.neis_school_collector import SchoolMetadata
from app.collectors.seoul_subway_collector import SubwayUsage
from app.db.database import save_commercial_store_snapshot
from app.db.models import CommercialStore


@dataclass(frozen=True)
class TradeSummary:
    apartment_name: str
    deal_ym: str
    trade_count: int
    avg_deal_amount: int | None
    avg_price_per_pyeong: int | None
    price_change_rate: float | None


@dataclass(frozen=True)
class FacilitySummary:
    radius_m: int
    convenience_stores: int
    cafes: int
    hospitals: int
    pharmacies: int
    restaurants: int
    academies: int
    large_marts: int
    parks: int
    starbucks: int
    chicken_shops: int


@dataclass(frozen=True)
class NearbySchool:
    name: str
    school_kind: str
    distance_m: int | None
    address: str | None


@dataclass(frozen=True)
class SchoolSummary:
    total_count: int
    elementary: NearbySchool | None
    middle: NearbySchool | None
    high: NearbySchool | None


@dataclass(frozen=True)
class TransitSummary:
    station_name: str | None
    distance_m: int | None
    line_name: str | None
    use_date: str | None
    daily_passengers: int | None


@dataclass(frozen=True)
class CategoryCount:
    name: str
    count: int


@dataclass(frozen=True)
class CommercialSummary:
    total_stores: int | None
    category_count: int | None
    top_categories: list[CategoryCount]
    previous_snapshot_date: str | None
    new_store_count: int | None
    closed_store_count: int | None

    @property
    def net_change(self) -> int | None:
        if self.new_store_count is None or self.closed_store_count is None:
            return None
        return self.new_store_count - self.closed_store_count


@dataclass(frozen=True)
class ScoreSummary:
    transport: int
    convenience: int
    school: int
    medical: int
    commercial: int
    overall: int


@dataclass(frozen=True)
class ResidentRatings:
    newlywed: int
    single_household: int
    family: int
    investment: int


@dataclass(frozen=True)
class ApartmentLivingReport:
    apartment_name: str
    address: str | None
    longitude: float
    latitude: float
    radius_m: int
    snapshot_date: str
    trade: TradeSummary
    facilities: FacilitySummary
    schools: SchoolSummary
    transit: TransitSummary
    commercial: CommercialSummary
    scores: ScoreSummary
    ratings: ResidentRatings
    warnings: list[str]


def analyze_apartment_trades(
    conn: sqlite3.Connection,
    lawd_cd: str,
    apartment_name: str,
    deal_ym: str,
) -> TradeSummary:
    resolved_name = _resolve_apartment_name(conn, lawd_cd, apartment_name) or apartment_name
    current = _trade_month_summary(conn, lawd_cd, resolved_name, deal_ym)
    previous = _trade_month_summary(conn, lawd_cd, resolved_name, previous_month(deal_ym))
    return TradeSummary(
        apartment_name=resolved_name,
        deal_ym=deal_ym,
        trade_count=current["count"],
        avg_deal_amount=current["avg_amount"],
        avg_price_per_pyeong=current["avg_price_per_pyeong"],
        price_change_rate=change_rate(current["avg_amount"], previous["avg_amount"]),
    )


def build_facility_summary(radius_m: int, results: Mapping[str, PlaceSearchResult]) -> FacilitySummary:
    return FacilitySummary(
        radius_m=radius_m,
        convenience_stores=_count(results, "convenience_store"),
        cafes=_count(results, "cafe"),
        hospitals=_count(results, "hospital"),
        pharmacies=_count(results, "pharmacy"),
        restaurants=_count(results, "restaurant"),
        academies=_count(results, "academy"),
        large_marts=_count(results, "large_mart"),
        parks=_count(results, "park"),
        starbucks=_count(results, "starbucks"),
        chicken_shops=_count(results, "chicken"),
    )


def build_facility_summary_from_stores(
    radius_m: int,
    stores: list[CommercialStore],
) -> FacilitySummary:
    def count_matching(*keywords: str) -> int:
        count = 0
        for store in stores:
            category = " ".join(
                part
                for part in (store.category_large, store.category_middle, store.category_small)
                if part
            )
            if any(keyword in category for keyword in keywords):
                count += 1
        return count

    return FacilitySummary(
        radius_m=radius_m,
        convenience_stores=count_matching("편의점"),
        cafes=count_matching("카페", "커피"),
        hospitals=count_matching("병원", "의원"),
        pharmacies=count_matching("약국"),
        restaurants=count_matching("음식", "한식", "중식", "일식", "양식"),
        academies=count_matching("학원", "교습"),
        large_marts=count_matching("대형마트", "슈퍼마켓"),
        parks=0,
        starbucks=0,
        chicken_shops=count_matching("치킨", "닭"),
    )


def build_school_summary(
    result: PlaceSearchResult | None,
    metadata: Mapping[str, SchoolMetadata],
) -> SchoolSummary:
    places = result.places if result else []
    schools = [_nearby_school(place, metadata.get(place.name)) for place in places]
    return SchoolSummary(
        total_count=result.total_count if result else 0,
        elementary=_nearest_school(schools, "초등학교"),
        middle=_nearest_school(schools, "중학교"),
        high=_nearest_school(schools, "고등학교"),
    )


def build_transit_summary(
    subway_result: PlaceSearchResult | None,
    usage: SubwayUsage | None,
) -> TransitSummary:
    nearest = subway_result.places[0] if subway_result and subway_result.places else None
    return TransitSummary(
        station_name=nearest.name if nearest else None,
        distance_m=nearest.distance_m if nearest else None,
        line_name=usage.line_name if usage else None,
        use_date=usage.use_date if usage else None,
        daily_passengers=usage.total_count if usage else None,
    )


def analyze_commercial_snapshot(
    conn: sqlite3.Connection,
    apartment_name: str,
    radius_m: int,
    snapshot_date: str,
    stores: list[CommercialStore] | None,
) -> CommercialSummary:
    if stores is None:
        return CommercialSummary(None, None, [], None, None, None)

    previous_date_row = conn.execute(
        """
        SELECT MAX(snapshot_date) AS snapshot_date
        FROM commercial_store_snapshot
        WHERE apartment_name = ? AND radius_m = ? AND snapshot_date < ?
        """,
        (apartment_name, radius_m, snapshot_date),
    ).fetchone()
    previous_date = previous_date_row["snapshot_date"] if previous_date_row else None
    previous_ids: set[str] = set()
    if previous_date:
        previous_ids = {
            row["business_id"]
            for row in conn.execute(
                """
                SELECT business_id FROM commercial_store_snapshot
                WHERE apartment_name = ? AND radius_m = ? AND snapshot_date = ?
                """,
                (apartment_name, radius_m, previous_date),
            ).fetchall()
        }

    save_commercial_store_snapshot(conn, apartment_name, radius_m, snapshot_date, stores)
    current_ids = {store.business_id for store in stores}
    categories = Counter(store.category_large or "기타" for store in stores)
    top_categories = [CategoryCount(name=name, count=count) for name, count in categories.most_common(5)]

    return CommercialSummary(
        total_stores=len(stores),
        category_count=len(categories),
        top_categories=top_categories,
        previous_snapshot_date=previous_date,
        new_store_count=len(current_ids - previous_ids) if previous_date else None,
        closed_store_count=len(previous_ids - current_ids) if previous_date else None,
    )


def calculate_scores(
    trade: TradeSummary,
    facilities: FacilitySummary,
    schools: SchoolSummary,
    transit: TransitSummary,
    commercial: CommercialSummary,
) -> tuple[ScoreSummary, ResidentRatings]:
    transport = _transport_score(transit)
    convenience = round(
        _average(
            _count_score(facilities.convenience_stores, 15),
            _count_score(facilities.cafes, 40),
            _count_score(facilities.restaurants, 80),
            _count_score(facilities.large_marts, 2),
            _count_score(facilities.parks, 3),
        )
    )
    school = round(
        _average(
            _distance_score(schools.elementary.distance_m if schools.elementary else None),
            _distance_score(schools.middle.distance_m if schools.middle else None),
            _distance_score(schools.high.distance_m if schools.high else None),
        )
    )
    medical = round(
        _average(
            _count_score(facilities.hospitals, 20),
            _count_score(facilities.pharmacies, 10),
        )
    )
    commercial_score = _commercial_score(commercial)
    overall = round(
        transport * 0.25
        + convenience * 0.25
        + school * 0.20
        + medical * 0.15
        + commercial_score * 0.15
    )
    scores = ScoreSummary(transport, convenience, school, medical, commercial_score, overall)

    market_score = _market_score(trade)
    ratings = ResidentRatings(
        newlywed=_stars(_average(transport, convenience, medical, school)),
        single_household=_stars(_average(transport, convenience, commercial_score)),
        family=_stars(_average(school, medical, convenience, transport)),
        investment=_stars(_average(market_score, transport, commercial_score)),
    )
    return scores, ratings


def _resolve_apartment_name(conn: sqlite3.Connection, lawd_cd: str, value: str) -> str | None:
    exact = conn.execute(
        "SELECT apartment_name FROM apartment_trade WHERE lawd_cd = ? AND apartment_name = ? LIMIT 1",
        (lawd_cd, value),
    ).fetchone()
    if exact:
        return str(exact["apartment_name"])
    row = conn.execute(
        """
        SELECT apartment_name, COUNT(*) AS trade_count
        FROM apartment_trade
        WHERE lawd_cd = ? AND apartment_name LIKE ?
        GROUP BY apartment_name
        ORDER BY trade_count DESC
        LIMIT 1
        """,
        (lawd_cd, f"%{value}%"),
    ).fetchone()
    return str(row["apartment_name"]) if row else None


def _trade_month_summary(
    conn: sqlite3.Connection,
    lawd_cd: str,
    apartment_name: str,
    deal_ym: str,
) -> dict[str, int | None]:
    row = conn.execute(
        """
        SELECT
            COUNT(*) AS trade_count,
            ROUND(AVG(deal_amount)) AS avg_amount,
            ROUND(AVG(deal_amount / (exclusive_area / ?))) AS avg_price_per_pyeong
        FROM apartment_trade
        WHERE lawd_cd = ? AND apartment_name = ? AND deal_ym = ?
          AND deal_amount IS NOT NULL AND exclusive_area > 0
        """,
        (PYEONG_IN_SQUARE_METERS, lawd_cd, apartment_name, deal_ym),
    ).fetchone()
    return {
        "count": int(row["trade_count"] or 0),
        "avg_amount": int(row["avg_amount"]) if row["avg_amount"] else None,
        "avg_price_per_pyeong": int(row["avg_price_per_pyeong"]) if row["avg_price_per_pyeong"] else None,
    }


def _nearby_school(place: LocalPlace, metadata: SchoolMetadata | None) -> NearbySchool:
    school_kind = metadata.school_kind if metadata and metadata.school_kind else _school_kind_from_name(place.name)
    return NearbySchool(
        name=place.name,
        school_kind=school_kind,
        distance_m=place.distance_m,
        address=(metadata.address if metadata else None) or place.road_address or place.address,
    )


def _school_kind_from_name(name: str) -> str:
    for kind in ("초등학교", "중학교", "고등학교"):
        if kind in name:
            return kind
    return "기타학교"


def _nearest_school(schools: list[NearbySchool], kind: str) -> NearbySchool | None:
    matches = [school for school in schools if kind in school.school_kind or kind in school.name]
    return min(matches, key=lambda school: school.distance_m if school.distance_m is not None else 999999) if matches else None


def _count(results: Mapping[str, PlaceSearchResult], key: str) -> int:
    result = results.get(key)
    return result.total_count if result else 0


def _count_score(count: int, target: int) -> int:
    return min(100, round(count / target * 100)) if target else 0


def _distance_score(distance_m: int | None) -> int:
    if distance_m is None:
        return 35
    if distance_m <= 500:
        return 100
    if distance_m <= 800:
        return 90
    if distance_m <= 1200:
        return 75
    if distance_m <= 2000:
        return 55
    return 35


def _transport_score(transit: TransitSummary) -> int:
    access = _distance_score(transit.distance_m)
    if transit.daily_passengers is None:
        return access
    usage = min(100, round(transit.daily_passengers / 50000 * 100))
    return round(access * 0.7 + usage * 0.3)


def _commercial_score(commercial: CommercialSummary) -> int:
    if commercial.total_stores is None or commercial.category_count is None:
        return 50
    density = _count_score(commercial.total_stores, 150)
    diversity = _count_score(commercial.category_count, 8)
    growth = 50
    if commercial.net_change is not None:
        growth = max(0, min(100, 50 + commercial.net_change * 5))
    return round(density * 0.5 + diversity * 0.3 + growth * 0.2)


def _market_score(trade: TradeSummary) -> int:
    volume = _count_score(trade.trade_count, 5)
    momentum = 50 if trade.price_change_rate is None else max(0, min(100, round(50 + trade.price_change_rate * 4)))
    return round(_average(volume, momentum))


def _average(*values: int | float) -> float:
    return sum(values) / len(values) if values else 0


def _stars(score: float) -> int:
    return max(1, min(5, round(score / 20)))
