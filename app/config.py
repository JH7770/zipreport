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
    kakao_rest_api_key: str
    commercial_district_endpoint: str
    neis_api_key: str
    seoul_open_data_key: str
    reb_api_key: str
    reb_statbl_id: str
    reb_cycle: str
    exim_api_key: str
    ecos_api_key: str
    kis_app_key: str
    kis_app_secret: str
    kis_base_url: str
    naver_client_id: str
    naver_client_secret: str
    wordpress_url: str
    wordpress_username: str
    wordpress_app_password: str
    default_status: str
    database_path: Path
    llm_api_key: str
    llm_model: str
    llm_base_url: str


def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        public_data_api_key=os.getenv("PUBLIC_DATA_API_KEY", ""),
        kakao_rest_api_key=os.getenv("KAKAO_REST_API_KEY", ""),
        commercial_district_endpoint=os.getenv(
            "COMMERCIAL_DISTRICT_ENDPOINT",
            "https://apis.data.go.kr/B553077/api/open/sdsc2/storeListInRadius",
        ),
        neis_api_key=os.getenv("NEIS_API_KEY", ""),
        seoul_open_data_key=os.getenv("SEOUL_OPEN_DATA_KEY", ""),
        reb_api_key=os.getenv("REB_API_KEY", ""),
        reb_statbl_id=os.getenv("REB_STATBL_ID", ""),
        reb_cycle=os.getenv("REB_CYCLE", "MM"),
        exim_api_key=os.getenv("EXIM_API_KEY", ""),
        ecos_api_key=os.getenv("ECOS_API_KEY", ""),
        kis_app_key=os.getenv("KIS_APP_KEY", ""),
        kis_app_secret=os.getenv("KIS_APP_SECRET", ""),
        kis_base_url=os.getenv("KIS_BASE_URL", "https://openapi.koreainvestment.com:9443").rstrip("/"),
        naver_client_id=os.getenv("NAVER_CLIENT_ID", ""),
        naver_client_secret=os.getenv("NAVER_CLIENT_SECRET", ""),
        wordpress_url=os.getenv("WORDPRESS_URL", "").rstrip("/"),
        wordpress_username=os.getenv("WORDPRESS_USERNAME", ""),
        wordpress_app_password=os.getenv("WORDPRESS_APP_PASSWORD", ""),
        default_status=os.getenv("DEFAULT_STATUS", "draft"),
        database_path=PROJECT_ROOT / os.getenv("DATABASE_PATH", "data/app.db"),
        llm_api_key=os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", "")),
        llm_model=os.getenv("LLM_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini")),
        llm_base_url=os.getenv("LLM_BASE_URL", os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/"),
    )


REGIONS = {
    "11500": {"sido": "서울특별시", "sigungu": "강서구"},
    "11470": {"sido": "서울특별시", "sigungu": "양천구"},
    "11440": {"sido": "서울특별시", "sigungu": "마포구"},
    "11560": {"sido": "서울특별시", "sigungu": "영등포구"},
    "11620": {"sido": "서울특별시", "sigungu": "관악구"},
    "11740": {"sido": "서울특별시", "sigungu": "강동구"},
}
