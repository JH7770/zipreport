from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.db.database import connect, initialize, save_wordpress_post
from app.publishers.wordpress_publisher import WordpressPublisher, extract_title
from app.quality.content_audit import audit_markdown_file, format_audit_result


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish a generated markdown report to WordPress.")
    parser.add_argument("--file", required=True, type=Path, help="Markdown file path")
    parser.add_argument("--status", help="WordPress post status. default comes from DEFAULT_STATUS")
    parser.add_argument("--category", action="append", type=int, default=[], help="WordPress category ID")
    parser.add_argument("--tag", action="append", type=int, default=[], help="WordPress tag ID")
    parser.add_argument("--tag-name", action="append", default=[], help="WordPress tag name to lookup or create")
    parser.add_argument("--slug", help="WordPress post slug")
    parser.add_argument("--excerpt", help="WordPress post excerpt")
    parser.add_argument("--featured-image", type=Path, help="Image path to upload as the WordPress featured image.")
    parser.add_argument("--skip-audit", action="store_true", help="Skip Markdown quality audit before publishing.")
    args = parser.parse_args()

    if not args.skip_audit:
        audit = audit_markdown_file(args.file)
        print(format_audit_result(audit))
        if not audit.passed:
            raise SystemExit(1)

    settings = get_settings()
    publisher = WordpressPublisher(
        settings.wordpress_url,
        settings.wordpress_username,
        settings.wordpress_app_password,
    )
    tag_ids = list(args.tag)
    if args.tag_name:
        tag_ids.extend(publisher.get_or_create_tags(args.tag_name))

    result = publisher.publish_markdown_file(
        args.file,
        status=args.status or settings.default_status,
        categories=args.category,
        tags=tag_ids,
        featured_image_path=args.featured_image,
        slug=args.slug,
        excerpt=args.excerpt,
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
