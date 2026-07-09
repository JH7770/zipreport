from __future__ import annotations

import argparse
import mimetypes
from pathlib import Path
import sys

import requests

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.publishers.wordpress_publisher import WordpressPublisher, extract_title, markdown_to_basic_html


def main() -> None:
    parser = argparse.ArgumentParser(description="Update an existing WordPress post from Markdown.")
    parser.add_argument("--post-id", required=True, type=int)
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--featured-image", type=Path)
    parser.add_argument("--excerpt")
    parser.add_argument("--tag", action="append", type=int, default=[], help="WordPress tag ID")
    parser.add_argument("--tag-name", action="append", default=[], help="WordPress tag name to lookup or create")
    parser.add_argument("--delete-old-featured", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    auth = (settings.wordpress_username, settings.wordpress_app_password)
    post_url = f"{settings.wordpress_url}/?rest_route=/wp/v2/posts/{args.post_id}"
    publisher = WordpressPublisher(
        settings.wordpress_url,
        settings.wordpress_username,
        settings.wordpress_app_password,
    )

    current = requests.get(f"{post_url}&context=edit", auth=auth, timeout=30)
    current.raise_for_status()
    old_media = current.json().get("featured_media")

    featured_media = None
    if args.featured_image is not None:
        featured_media = _upload_media(settings.wordpress_url, auth, args.featured_image)

    markdown = args.file.read_text(encoding="utf-8")
    payload = {
        "title": extract_title(markdown),
        "content": markdown_to_basic_html(markdown),
        "status": "draft",
    }
    if args.excerpt:
        payload["excerpt"] = args.excerpt
    tag_ids = list(args.tag)
    if args.tag_name:
        tag_ids.extend(publisher.get_or_create_tags(args.tag_name))
    if tag_ids:
        payload["tags"] = tag_ids
    if featured_media is not None:
        payload["featured_media"] = featured_media

    updated = requests.post(post_url, json=payload, auth=auth, timeout=60)
    updated.raise_for_status()

    delete_status = "skipped"
    if args.delete_old_featured and old_media and old_media != featured_media:
        deleted = requests.delete(
            f"{settings.wordpress_url}/?rest_route=/wp/v2/media/{old_media}&force=true",
            auth=auth,
            timeout=30,
        )
        delete_status = str(deleted.status_code)

    data = updated.json()
    print(f"Updated WordPress post {data.get('id')}: {data.get('link')}")
    print(f"featured_media={featured_media} old_media={old_media} delete_old_media={delete_status}")


def _upload_media(base_url: str, auth: tuple[str, str], image_path: Path) -> int:
    if not image_path.exists():
        raise FileNotFoundError(f"Featured image does not exist: {image_path}")
    mime_type = mimetypes.guess_type(str(image_path))[0] or "image/png"
    headers = {
        "Content-Disposition": f'attachment; filename="{image_path.name}"',
        "Content-Type": mime_type,
    }
    response = requests.post(
        f"{base_url}/?rest_route=/wp/v2/media",
        data=image_path.read_bytes(),
        headers=headers,
        auth=auth,
        timeout=60,
    )
    response.raise_for_status()
    return int(response.json()["id"])


if __name__ == "__main__":
    main()
