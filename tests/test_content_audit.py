from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.quality.content_audit import audit_markdown, audit_markdown_file


class ContentAuditTest(unittest.TestCase):
    def test_clean_korean_report_passes(self) -> None:
        markdown = """# 2026년 5월 강서구 아파트 실거래가 리포트

2026년 5월 거래량은 전월 대비 +10.5% 변동했습니다.

| 순위 | 단지명 | 거래건수 |
|---:|---|---:|
| 1 | 테스트아파트 | 3 |

본 글은 공공 실거래 자료를 정리한 참고 자료이며 투자 추천이 아닙니다.
"""

        result = audit_markdown(markdown)

        self.assertTrue(result.passed)
        self.assertEqual(result.errors, ())

    def test_mojibake_fails(self) -> None:
        markdown = """# ?꾪뙆???ㅺ굅?섍? 由ы룷??

거래 참고 자료입니다.
"""

        result = audit_markdown(markdown)

        self.assertFalse(result.passed)
        self.assertEqual(result.errors[0].code, "mojibake")

    def test_unrendered_template_fails(self) -> None:
        result = audit_markdown("# 제목\n\n{{ report.title }}\n\n참고 자료입니다.")

        self.assertFalse(result.passed)
        self.assertEqual(result.errors[0].code, "unrendered_template")

    def test_table_column_mismatch_fails(self) -> None:
        markdown = """# 제목

| 순위 | 단지명 |
|---:|---|
| 1 | A | 3 |

참고 자료입니다.
"""

        result = audit_markdown(markdown)

        self.assertFalse(result.passed)
        self.assertEqual(result.errors[0].code, "table_columns")

    def test_audit_markdown_file_reads_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "report.md"
            path.write_text("\ufeff# 제목\n\n거래 +1.0% 참고 자료입니다.\n", encoding="utf-8")

            result = audit_markdown_file(path)

        self.assertTrue(result.passed)


if __name__ == "__main__":
    unittest.main()
