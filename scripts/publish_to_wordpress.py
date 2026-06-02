from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.db.database import connect, initialize, save_wordpress_post
from app.publishers.wordpress_publisher import WordpressPublisher, extract_title


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish a generated markdown report to WordPress.")
    parser.add_argument("--file", required=True, type=Path, help="Markdown file path")
    parser.add_argument("--status", help="WordPress post status. default comes from DEFAULT_STATUS")
    parser.add_argument("--category", action="append", type=int, default=[], help="WordPress category ID")
    parser.add_argument("--tag", action="append", type=int, default=[], help="WordPress tag ID")
    args = parser.parse_args()

    settings = get_settings()
    publisher = WordpressPublisher(
        settings.wordpress_url,
        settings.wordpress_username,
        settings.wordpress_app_password,
    )
    result = publisher.publish_markdown_file(
        args.file,
        status=args.status or settings.default_status,
        categories=args.category,
        tags=args.tag,
    )

    conn = connect(settings.database_path)
    initialize(conn)
    save_wordpress_post(
        conn,
        post_type="monthly_region_report",
        region="",
        deal_ym="",
        title=extract_title(args.file.read_text(encoding="utf-8")),
        wordpress_post_id=result.post_id,
        status=result.status,
    )
    print(f"Published WordPress post {result.post_id}: {result.link or '(no link)'}")


if __name__ == "__main__":
    main()
