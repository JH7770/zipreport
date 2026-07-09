from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AuditIssue:
    severity: str
    code: str
    message: str
    line: int | None = None


@dataclass(frozen=True)
class AuditResult:
    path: Path | None
    issues: tuple[AuditIssue, ...]

    @property
    def errors(self) -> tuple[AuditIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "error")

    @property
    def warnings(self) -> tuple[AuditIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "warning")

    @property
    def passed(self) -> bool:
        return not self.errors


MOJIBAKE_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\uFFFD", "replacement character found"),
    (r"[?][ㄱ-ㅎㅏ-ㅣ가-힣]", "question-mark mojibake fragment found"),
    (r"(?:ì|ë|í|ê|à|á|â|ã|ä|å|æ|ç|è|é){2,}", "latin mojibake fragment found"),
    (r"(?:留|吏|理|嫄|由ы|諛|怨꾩|援먰|媛뺤|\?쒖|\?꾪|\?ㅺ)", "cp949 mojibake fragment found"),
)

DISCLAIMER_HINTS = ("추천", "투자", "참고", "자료", "실거래")


def audit_markdown_file(path: Path) -> AuditResult:
    return audit_markdown(path.read_text(encoding="utf-8"), path)


def audit_markdown(markdown: str, path: Path | None = None) -> AuditResult:
    markdown = markdown.lstrip("\ufeff")
    issues: list[AuditIssue] = []
    lines = markdown.splitlines()

    if not markdown.strip():
        issues.append(AuditIssue("error", "empty_document", "Markdown document is empty."))
        return AuditResult(path, tuple(issues))

    _audit_mojibake(lines, issues)
    _audit_structure(lines, issues)
    _audit_tables(lines, issues)
    _audit_links(lines, issues)
    _audit_content_hints(markdown, issues)

    return AuditResult(path, tuple(issues))


def _audit_mojibake(lines: list[str], issues: list[AuditIssue]) -> None:
    for line_number, line in enumerate(lines, 1):
        for pattern, message in MOJIBAKE_PATTERNS:
            if re.search(pattern, line):
                issues.append(AuditIssue("error", "mojibake", message, line_number))
                break


def _audit_structure(lines: list[str], issues: list[AuditIssue]) -> None:
    title_lines = [index for index, line in enumerate(lines, 1) if line.startswith("# ")]
    if not title_lines:
        issues.append(AuditIssue("error", "missing_title", "Document has no level-1 Markdown title."))
    elif title_lines[0] > 8:
        issues.append(
            AuditIssue(
                "warning",
                "late_title",
                "The first level-1 title appears after a long metadata block.",
                title_lines[0],
            )
        )

    if any(token in "\n".join(lines) for token in ("{{", "}}", "{%", "%}")):
        issues.append(AuditIssue("error", "unrendered_template", "Unrendered template syntax remains."))

    body_lines = [line for line in lines if line.strip() and not line.startswith("#")]
    if len(body_lines) < 2:
        issues.append(AuditIssue("warning", "thin_body", "Document body is very short."))


def _audit_tables(lines: list[str], issues: list[AuditIssue]) -> None:
    table_block: list[tuple[int, str]] = []
    for line_number, line in enumerate(lines + [""], 1):
        if line.strip().startswith("|") and "|" in line.strip()[1:]:
            table_block.append((line_number, line))
            continue
        if table_block:
            _audit_table_block(table_block, issues)
            table_block = []


def _audit_table_block(block: list[tuple[int, str]], issues: list[AuditIssue]) -> None:
    rows = [(line_number, _split_table_row(line)) for line_number, line in block]
    data_rows = [(line_number, cells) for line_number, cells in rows if not _is_separator_row(cells)]
    if len(data_rows) < 2:
        return

    expected_columns = len(data_rows[0][1])
    for line_number, cells in data_rows[1:]:
        if len(cells) != expected_columns:
            issues.append(
                AuditIssue(
                    "error",
                    "table_columns",
                    f"Markdown table has {len(cells)} columns; expected {expected_columns}.",
                    line_number,
                )
            )


def _split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def _audit_links(lines: list[str], issues: list[AuditIssue]) -> None:
    for line_number, line in enumerate(lines, 1):
        if re.search(r"\[[^\]]+\]\(\s*\)", line):
            issues.append(AuditIssue("error", "empty_link", "Markdown link has an empty URL.", line_number))
        if re.search(r"https?://[^\s)]+[.,](?:\s|$)", line):
            issues.append(
                AuditIssue(
                    "warning",
                    "link_punctuation",
                    "A URL may include trailing punctuation.",
                    line_number,
                )
            )


def _audit_content_hints(markdown: str, issues: list[AuditIssue]) -> None:
    if not any(hint in markdown for hint in DISCLAIMER_HINTS):
        issues.append(
            AuditIssue(
                "warning",
                "missing_disclaimer_hint",
                "No obvious data-source or investment-disclaimer wording found.",
            )
        )

    if not re.search(r"\d+(?:\.\d+)?%", markdown) and "거래" in markdown:
        issues.append(AuditIssue("warning", "missing_percent", "Trade report has no visible percentage value."))


def format_audit_result(result: AuditResult) -> str:
    label = str(result.path) if result.path else "<markdown>"
    if not result.issues:
        return f"PASS {label}"

    rows = [f"{'PASS' if result.passed else 'FAIL'} {label}"]
    for issue in result.issues:
        location = f":{issue.line}" if issue.line is not None else ""
        rows.append(f"- {issue.severity.upper()} {issue.code}{location}: {issue.message}")
    return "\n".join(rows)
