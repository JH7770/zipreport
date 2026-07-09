from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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
from app.publishers import wordpress_publisher
from app.publishers.wordpress_publisher import WordpressPublisher, markdown_to_basic_html


class FakeResponse:
    def __init__(self, status_code: int, payload: object) -> None:
        self.status_code = status_code
        self.payload = payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> object:
        return self.payload


class FakeRequests:
    def __init__(
        self,
        calls: list[str],
        route: str,
        payload: dict[str, object],
        get_payload: list[dict[str, object]] | None = None,
    ) -> None:
        self.calls = calls
        self.route = route
        self.payload = payload
        self.get_payload = get_payload if get_payload is not None else []

    def post(self, endpoint: str, **kwargs: object) -> FakeResponse:
        self.calls.append(endpoint)
        if endpoint.endswith(f"/wp-json/wp/v2/{self.route}"):
            return FakeResponse(404, {})
        return FakeResponse(201, self.payload)

    def get(self, endpoint: str, **_: object) -> FakeResponse:
        self.calls.append(endpoint)
        if endpoint.startswith("https://example.com/wp-json/wp/v2/"):
            return FakeResponse(404, {})
        return FakeResponse(200, self.get_payload)


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

    def test_wordpress_publish_falls_back_to_rest_route(self) -> None:
        calls: list[str] = []

        with tempfile.TemporaryDirectory() as tmpdir:
            post_path = Path(tmpdir) / "post.md"
            post_path.write_text("# 테스트 제목\n\n본문입니다.", encoding="utf-8")

            fake_requests = FakeRequests(
                calls,
                route="posts",
                payload={"id": 42, "link": "https://example.com/?p=42", "status": "draft"},
            )
            with mock.patch.object(wordpress_publisher, "requests", fake_requests):
                result = WordpressPublisher("https://example.com", "user", "pass").publish_markdown_file(post_path)

        self.assertEqual(result.post_id, 42)
        self.assertEqual(calls[0], "https://example.com/wp-json/wp/v2/posts")
        self.assertEqual(calls[1], "https://example.com/?rest_route=/wp/v2/posts")

    def test_wordpress_media_upload_falls_back_to_rest_route(self) -> None:
        calls: list[str] = []

        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = Path(tmpdir) / "featured.png"
            image_path.write_bytes(b"\x89PNG\r\n\x1a\n")

            fake_requests = FakeRequests(
                calls,
                route="media",
                payload={"id": 7, "link": "https://example.com/featured.png"},
            )
            with mock.patch.object(wordpress_publisher, "requests", fake_requests):
                result = WordpressPublisher("https://example.com", "user", "pass").upload_media(image_path)

        self.assertEqual(result.media_id, 7)
        self.assertEqual(calls[0], "https://example.com/wp-json/wp/v2/media")
        self.assertEqual(calls[1], "https://example.com/?rest_route=/wp/v2/media")

    def test_wordpress_tag_lookup_falls_back_to_rest_route(self) -> None:
        calls: list[str] = []

        fake_requests = FakeRequests(
            calls,
            route="tags",
            payload={"id": 9, "name": "실거래가"},
            get_payload=[{"id": 9, "name": "실거래가"}],
        )
        with mock.patch.object(wordpress_publisher, "requests", fake_requests):
            tag_id = WordpressPublisher("https://example.com", "user", "pass").get_or_create_term("tags", "실거래가")

        self.assertEqual(tag_id, 9)
        self.assertIn("search=%EC%8B%A4%EA%B1%B0%EB%9E%98%EA%B0%80", calls[1])

    def test_markdown_links_convert_to_external_anchors(self) -> None:
        html = markdown_to_basic_html("# 제목\n\n[지도](https://map.naver.com/p/search/test) 링크입니다.")

        self.assertIn(
            '<a href="https://map.naver.com/p/search/test" target="_blank" rel="noopener noreferrer">지도</a>',
            html,
        )

    def test_markdown_converts_level_three_heading(self) -> None:
        html = markdown_to_basic_html("# Title\n\n## Region\n\n### Commute")

        self.assertIn("<h3>Commute</h3>", html)

    def test_markdown_groups_multiline_blockquote(self) -> None:
        html = markdown_to_basic_html("# Title\n\n> First line\n>\n> Second line\n\nBody")

        self.assertIn("<blockquote>\n<p>First line</p>\n<p>Second line</p>\n</blockquote>", html)
        self.assertEqual(html.count("<blockquote>"), 1)
        self.assertNotIn("<p></p>", html)

    def test_markdown_bullet_list_converts_to_unordered_list(self) -> None:
        html = markdown_to_basic_html(
            "# 제목\n\n- **신축**: 2021년 이후\n- [지도](https://map.kakao.com/link/search/test)"
        )

        self.assertIn("<ul>", html)
        self.assertIn("<li><strong>신축</strong>: 2021년 이후</li>", html)
        self.assertIn(
            '<li><a href="https://map.kakao.com/link/search/test" target="_blank" rel="noopener noreferrer">지도</a></li>',
            html,
        )
        self.assertNotIn("<p>- ", html)

    def test_markdown_ignores_internal_metadata_before_title(self) -> None:
        html = markdown_to_basic_html(
            "제목: 내부 제목\n\n슬러그: internal-slug\n\n태그: 내부태그\n\n---\n\n# 공개 제목\n\n공개 본문"
        )

        self.assertNotIn("내부 제목", html)
        self.assertNotIn("internal-slug", html)
        self.assertNotIn("내부태그", html)
        self.assertIn("<h1>공개 제목</h1>", html)
        self.assertIn("<p>공개 본문</p>", html)


if __name__ == "__main__":
    unittest.main()
