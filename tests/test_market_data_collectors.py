from __future__ import annotations

import unittest

from app.collectors.molit_rent_collector import parse_rent_xml
from app.collectors.ecos_collector import parse_ecos_statistics
from app.collectors.exim_exchange_collector import parse_exchange_rates
from app.collectors.kis_quote_collector import parse_kis_domestic_price
from app.collectors.naver_datalab_collector import parse_search_trends
from app.collectors.reb_statistics_collector import parse_reb_statistics
from app.collectors.region_code_collector import parse_region_code_json


class MarketDataCollectorTest(unittest.TestCase):
    def test_parse_rent_xml(self) -> None:
        xml = """
        <response>
          <header><resultCode>00</resultCode><resultMsg>OK</resultMsg></header>
          <body>
            <totalCount>1</totalCount>
            <items>
              <item>
                <dealYear>2026</dealYear>
                <dealMonth>5</dealMonth>
                <dealDay>10</dealDay>
                <umdNm>Test-dong</umdNm>
                <aptNm>Test Apt</aptNm>
                <excluUseAr>84.90</excluUseAr>
                <deposit>70,000</deposit>
                <monthlyRent>0</monthlyRent>
                <floor>12</floor>
                <buildYear>2014</buildYear>
              </item>
            </items>
          </body>
        </response>
        """

        rents, total_count = parse_rent_xml(xml, "11500", "202605")

        self.assertEqual(total_count, 1)
        self.assertEqual(len(rents), 1)
        self.assertEqual(rents[0].deal_ym, "202605")
        self.assertEqual(rents[0].deposit_amount, 700000000)
        self.assertEqual(rents[0].monthly_rent, 0)

    def test_parse_region_code_json(self) -> None:
        payload = {
            "StanReginCd": [
                {"head": [{"totalCount": 1}]},
                {
                    "row": [
                        {
                            "region_cd": "1150000000",
                            "sido_cd": "11",
                            "sgg_cd": "500",
                            "locatadd_nm": "Seoul Gangseo-gu",
                        }
                    ]
                },
            ]
        }

        regions, total_count = parse_region_code_json(payload)

        self.assertEqual(total_count, 1)
        self.assertEqual(regions[0].lawd_cd, "11500")
        self.assertEqual(regions[0].sido, "Seoul")

    def test_parse_reb_statistics(self) -> None:
        payload = {
            "SttsApiTblData": [
                {"head": [{"list_total_count": 1}]},
                {
                    "row": [
                        {
                            "STATBL_ID": "A_TEST",
                            "DTACYCLE_CD": "MM",
                            "WRTTIME_IDTFR_ID": "202605",
                            "CLS_NM": "Seoul",
                            "ITM_NM": "Apartment index",
                            "DTA_VAL": "101.7",
                        }
                    ]
                },
            ]
        }

        rows = parse_reb_statistics(payload)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].statbl_id, "A_TEST")
        self.assertEqual(rows[0].value, 101.7)

    def test_parse_exchange_rates(self) -> None:
        rows = parse_exchange_rates(
            [
                {
                    "result": 1,
                    "cur_unit": "USD",
                    "cur_nm": "US Dollar",
                    "deal_bas_r": "1,370.50",
                    "ttb": "1,357.00",
                    "tts": "1,384.00",
                }
            ],
            "20260609",
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].source, "EXIM")
        self.assertEqual(rows[0].currency_unit, "USD")
        self.assertEqual(rows[0].deal_bas_r, 1370.5)

    def test_parse_ecos_statistics(self) -> None:
        payload = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "731Y001",
                        "CYCLE": "D",
                        "TIME": "20260609",
                        "ITEM_CODE1": "0000001",
                        "ITEM_NAME1": "Base rate",
                        "DATA_VALUE": "3.25",
                    }
                ]
            }
        }

        rows = parse_ecos_statistics(payload)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].stat_code, "731Y001")
        self.assertEqual(rows[0].value, 3.25)

    def test_parse_kis_domestic_price(self) -> None:
        payload = {
            "rt_cd": "0",
            "output": {
                "hts_kor_isnm": "Samsung Electronics",
                "stck_bsop_date": "20260609",
                "stck_prpr": "75000",
                "prdy_vrss": "500",
                "prdy_ctrt": "0.67",
            },
        }

        quote = parse_kis_domestic_price(payload, "005930")

        self.assertEqual(quote.source, "KIS")
        self.assertEqual(quote.symbol, "005930")
        self.assertEqual(quote.price, 75000)

    def test_parse_search_trends(self) -> None:
        payload = {
            "results": [
                {
                    "title": "Apartment",
                    "keywords": ["apartment", "rent"],
                    "data": [{"period": "2026-06-09", "ratio": 83.5}],
                }
            ]
        }

        rows = parse_search_trends(payload)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].source, "NAVER_DATALAB")
        self.assertEqual(rows[0].period, "2026-06-09")
        self.assertEqual(rows[0].ratio, 83.5)


if __name__ == "__main__":
    unittest.main()
