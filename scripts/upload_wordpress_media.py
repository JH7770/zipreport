from __future__ import annotations

import argparse
import mimetypes
from pathlib import Path
import sys

import requests

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.config import get_settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload a media file to WordPress and print its URL.")
    parser.add_argument("file", type=Path)
    args = parser.parse_args()

    settings = get_settings()
    path = args.file
    mime_type = mimetypes.guess_type(str(path))[0] or "image/png"
    headers = {
        "Content-Disposition": f'attachment; filename="{path.name}"',
        "Content-Type": mime_type,
    }
    response = requests.post(
        f"{settings.wordpress_url}/?rest_route=/wp/v2/media",
        data=path.read_bytes(),
        headers=headers,
        auth=(settings.wordpress_username, settings.wordpress_app_password),
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    print(data.get("id"))
    print(data.get("source_url") or data.get("guid", {}).get("rendered") or data.get("link"))


if __name__ == "__main__":
    main()
