from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.analyzers.apartment_analyzer import analyze_month
from app.collectors.molit_trade_collector import parse_trade_xml
from app.db.database import initialize, insert_trades
from app.db.models import ApartmentTrade
from app.generators.post_generator import (
    render_apartment_detail_report,
    render_monthly_report,
    render_top_rising_report,
    write_markdown,
)


class PipelineTest(unittest.TestCase):
    def test_parse_trade_xml(self) -> None:
        xml = """
        <response>
          <header><resultCode>00</resultCode><resultMsg>OK</resultMsg></header>
          <body>
            <totalCount>1</totalCount>
            <items>
              <item>
                <dealYear>2026</dealYear>
                <dealMonth>5</dealMonth>
                <dealDay>12</dealDay>
                <umdNm>마곡동</umdNm>
                <aptNm>마곡엠밸리7단지</aptNm>
                <excluUseAr>84.90</excluUseAr>
                <dealAmount>117,500</dealAmount>
                <floor>14</floor>
                <buildYear>2014</buildYear>
              </item>
            </items>
          </body>
        </response>
        """
        trades, total_count = parse_trade_xml(xml, "11500", "202605")

        self.assertEqual(total_count, 1)
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].deal_ym, "202605")
        self.assertEqual(trades[0].deal_amount, 1175000000)

    def test_analyze_and_render_monthly_report(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        initialize(conn)
        insert_trades(
            conn,
            [
                ApartmentTrade("11500", "202604", 1, "마곡동", "A단지", 84.9, 1000000000, 3, 2010, "{}"),
                ApartmentTrade("11500", "202605", 2, "마곡동", "A단지", 84.9, 1100000000, 4, 2010, "{}"),
                ApartmentTrade("11500", "202605", 3, "등촌동", "B단지", 59.9, 700000000, 8, 2000, "{}"),
            ],
        )

        report = analyze_month(conn, "11500", "202605")
        markdown = render_monthly_report(report)

        self.assertEqual(report.total_count, 2)
        self.assertEqual(report.prev_total_count, 1)
        self.assertIn("서울특별시 강서구", markdown)
        self.assertIn("A단지", markdown)

    def test_generate_three_report_types(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        initialize(conn)
        insert_trades(
            conn,
            [
                ApartmentTrade("11500", "202604", 1, "마곡동", "A단지", 84.9, 1000000000, 3, 2010, "{}"),
                ApartmentTrade("11500", "202605", 2, "마곡동", "A단지", 84.9, 1100000000, 4, 2010, "{}"),
                ApartmentTrade("11500", "202605", 3, "마곡동", "A단지", 84.9, 1120000000, 8, 2010, "{}"),
            ],
        )
        report = analyze_month(conn, "11500", "202605")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            monthly = write_markdown(render_monthly_report(report), "monthly.md", output_dir)
            rising = write_markdown(render_top_rising_report(report), "rising.md", output_dir)
            detail = write_markdown(
                render_apartment_detail_report(report, report.top_volume_complexes[0]),
                "detail.md",
                output_dir,
            )

            self.assertTrue(monthly.exists())
            self.assertTrue(rising.exists())
            self.assertTrue(detail.exists())
            self.assertIn("상승률", rising.read_text(encoding="utf-8"))
            self.assertIn("거래 요약", detail.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
