from __future__ import annotations

import sqlite3
import unittest

from app.analyzers.apartment_living_analyzer import (
    ApartmentLivingReport,
    CommercialSummary,
    FacilitySummary,
    ResidentRatings,
    SchoolSummary,
    ScoreSummary,
    TradeSummary,
    TransitSummary,
    analyze_apartment_trades,
    analyze_commercial_snapshot,
)
from app.collectors.commercial_district_collector import parse_commercial_response
from app.collectors.kakao_local_collector import KakaoLocalCollector
from app.collectors.neis_school_collector import parse_school_response
from app.collectors.seoul_subway_collector import parse_subway_response
from app.db.database import initialize, insert_trades
from app.db.models import ApartmentTrade, CommercialStore
from app.generators.apartment_living_report import render_apartment_living_report


class FakeResponse:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self.payload


class ApartmentLivingReportTest(unittest.TestCase):
    def test_kakao_category_search_uses_total_count_and_paginates(self) -> None:
        calls: list[int] = []

        def fake_get(_: str, **kwargs: object) -> FakeResponse:
            params = kwargs["params"]
            page = int(params["page"])
            calls.append(page)
            return FakeResponse(
                {
                    "meta": {"total_count": 20, "is_end": page == 2},
                    "documents": [
                        {
                            "id": str(page),
                            "place_name": f"카페 {page}",
                            "x": "126.1",
                            "y": "37.1",
                            "distance": str(page * 100),
                        }
                    ],
                }
            )

        result = KakaoLocalCollector("key", http_get=fake_get).search_category("CE7", 126.1, 37.1, 1000)

        self.assertEqual(calls, [1, 2])
        self.assertEqual(result.total_count, 20)
        self.assertEqual([place.name for place in result.places], ["카페 1", "카페 2"])

    def test_parse_commercial_response(self) -> None:
        stores, total = parse_commercial_response(
            {
                "header": {"resultCode": "00"},
                "body": {
                    "totalCount": 1,
                    "items": [
                        {
                            "bizesId": "A1",
                            "bizesNm": "테스트카페",
                            "indsLclsNm": "음식",
                            "indsMclsNm": "카페",
                            "indsSclsNm": "커피전문점",
                            "lon": "126.1",
                            "lat": "37.1",
                        }
                    ],
                },
            }
        )

        self.assertEqual(total, 1)
        self.assertEqual(stores[0].business_id, "A1")
        self.assertEqual(stores[0].category_small, "커피전문점")

    def test_commercial_snapshot_compares_store_ids(self) -> None:
        conn = self._connection()
        first = [self._store("A"), self._store("B")]
        second = [self._store("B"), self._store("C")]

        baseline = analyze_commercial_snapshot(conn, "테스트아파트", 1000, "2026-06-01", first)
        current = analyze_commercial_snapshot(conn, "테스트아파트", 1000, "2026-06-14", second)

        self.assertIsNone(baseline.new_store_count)
        self.assertEqual(current.previous_snapshot_date, "2026-06-01")
        self.assertEqual(current.new_store_count, 1)
        self.assertEqual(current.closed_store_count, 1)
        self.assertEqual(current.net_change, 0)

    def test_trade_summary_and_price_per_pyeong(self) -> None:
        conn = self._connection()
        insert_trades(
            conn,
            [
                ApartmentTrade("11500", "202605", 1, "마곡동", "테스트아파트", 84.9, 1000000000, 3, 2020, "{}"),
                ApartmentTrade("11500", "202606", 1, "마곡동", "테스트아파트", 84.9, 1100000000, 4, 2020, "{}"),
            ],
        )

        summary = analyze_apartment_trades(conn, "11500", "테스트", "202606")

        self.assertEqual(summary.apartment_name, "테스트아파트")
        self.assertEqual(summary.trade_count, 1)
        self.assertEqual(summary.price_change_rate, 10.0)
        self.assertGreater(summary.avg_price_per_pyeong or 0, 40000000)

    def test_school_and_subway_parsers(self) -> None:
        schools = parse_school_response(
            {
                "schoolInfo": [
                    {"head": [{"list_total_count": 1}]},
                    {"row": [{"SCHUL_NM": "서울가곡초등학교", "SCHUL_KND_SC_NM": "초등학교", "ORG_RDNMA": "서울"}]},
                ]
            }
        )
        subway = parse_subway_response(
            {
                "CardSubwayStatsNew": {
                    "row": [
                        {
                            "USE_DT": "20260610",
                            "LINE_NUM": "5호선",
                            "SUB_STA_NM": "마곡",
                            "RIDE_PASGR_NUM": 10000,
                            "ALIGHT_PASGR_NUM": 11000,
                        }
                    ]
                }
            }
        )

        self.assertEqual(schools[0].school_kind, "초등학교")
        self.assertEqual(subway[0].total_count, 21000)

    def test_parse_current_seoul_subway_fields(self) -> None:
        subway = parse_subway_response(
            {
                "CardSubwayStatsNew": {
                    "row": [
                        {
                            "USE_YMD": "20260608",
                            "SBWY_ROUT_LN_NM": "9호선",
                            "SBWY_STNS_NM": "둔촌오륜",
                            "GTON_TNOPE": "5000",
                            "GTOFF_TNOPE": "5500",
                        }
                    ]
                }
            }
        )

        self.assertEqual(subway[0].station_name, "둔촌오륜")
        self.assertEqual(subway[0].total_count, 10500)

    def test_render_report_contains_scores_and_snapshot_caveat(self) -> None:
        report = ApartmentLivingReport(
            apartment_name="테스트아파트",
            address="서울특별시 강서구",
            longitude=126.1,
            latitude=37.1,
            radius_m=1000,
            snapshot_date="2026-06-14",
            trade=TradeSummary("테스트아파트", "202606", 2, 1000000000, 40000000, 3.0),
            facilities=FacilitySummary(1000, 10, 20, 5, 4, 30, 8, 1, 2, 1, 5),
            schools=SchoolSummary(3, None, None, None),
            transit=TransitSummary("마곡역", 500, "5호선", "20260610", 21000),
            commercial=CommercialSummary(100, 7, [], "2026-06-01", 4, 2),
            scores=ScoreSummary(90, 80, 70, 60, 75, 77),
            ratings=ResidentRatings(4, 4, 4, 3),
            warnings=[],
        )

        markdown = render_apartment_living_report(report)

        self.assertIn("**77점**", markdown)
        self.assertIn("개업·폐업 추정치", markdown)
        self.assertIn("마곡역", markdown)

    @staticmethod
    def _connection() -> sqlite3.Connection:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        initialize(conn)
        return conn

    @staticmethod
    def _store(business_id: str) -> CommercialStore:
        return CommercialStore(business_id, business_id, "음식", "카페", "커피", 126.1, 37.1, "{}")


if __name__ == "__main__":
    unittest.main()
