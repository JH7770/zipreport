from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_dotenv(path: Path | None = None) -> None:
    env_path = path or PROJECT_ROOT / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    public_data_api_key: str
    wordpress_url: str
    wordpress_username: str
    wordpress_app_password: str
    default_status: str
    database_path: Path


def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        public_data_api_key=os.getenv("PUBLIC_DATA_API_KEY", ""),
        wordpress_url=os.getenv("WORDPRESS_URL", "").rstrip("/"),
        wordpress_username=os.getenv("WORDPRESS_USERNAME", ""),
        wordpress_app_password=os.getenv("WORDPRESS_APP_PASSWORD", ""),
        default_status=os.getenv("DEFAULT_STATUS", "draft"),
        database_path=PROJECT_ROOT / os.getenv("DATABASE_PATH", "data/app.db"),
    )


REGIONS = {
    "11500": {"sido": "서울특별시", "sigungu": "강서구"},
    "11470": {"sido": "서울특별시", "sigungu": "양천구"},
    "11440": {"sido": "서울특별시", "sigungu": "마포구"},
    "11560": {"sido": "서울특별시", "sigungu": "영등포구"},
    "11620": {"sido": "서울특별시", "sigungu": "관악구"},
}
