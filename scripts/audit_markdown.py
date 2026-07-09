from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.quality.content_audit import audit_markdown_file, format_audit_result


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit generated Markdown reports before publication.")
    parser.add_argument("files", nargs="*", type=Path, help="Markdown files to audit. Defaults to output/*.md.")
    args = parser.parse_args()

    files = args.files or sorted((Path(__file__).resolve().parents[1] / "output").glob("*.md"))
    if not files:
        print("No Markdown files found to audit.")
        return

    failed = False
    for path in files:
        result = audit_markdown_file(path)
        print(format_audit_result(result))
        failed = failed or not result.passed

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
