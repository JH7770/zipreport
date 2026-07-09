# ZipReport

부동산 실거래가와 생활 인프라 데이터를 수집해 Markdown 리포트를 만들고, 필요하면 WordPress 초안으로 발행하는 Python 프로젝트입니다.

서울 주요 구의 아파트 매매/전월세 데이터를 SQLite에 저장한 뒤 월간 시장 리포트, 상승률 리포트, 단지 상세 리포트, 단지 생활권 리포트를 생성합니다. 일부 리포트는 LLM 문장 다듬기와 대표 이미지 생성도 지원합니다.

## 주요 기능

- 국토교통부 아파트 매매 실거래가 수집
- 국토교통부 아파트 전월세 실거래가 수집
- 한국부동산원(REB), 한국은행 ECOS, 한국수출입은행 환율, 한국투자증권 시세, 네이버 데이터랩 검색 트렌드 수집
- 카카오 로컬, 소상공인 상가업소, NEIS 학교, 서울 열린데이터 지하철 데이터를 활용한 단지 생활권 리포트 생성
- SQLite 기반 데이터 저장 및 중복 저장 방지
- Jinja2 템플릿 기반 Markdown 리포트 생성
- LLM을 이용한 Markdown 문장 다듬기
- Pillow 기반 대표 이미지 생성
- WordPress REST API 초안 발행, 태그 생성, 대표 이미지 업로드
- GitHub Actions 월간 자동 실행 워크플로

## 빠른 시작

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

`.env`에 필요한 API 키를 채운 뒤 스크립트를 실행합니다. API 없이 동작을 확인하려면 샘플 데이터를 먼저 적재할 수 있습니다.

```powershell
python scripts/load_sample_data.py
python scripts/generate_post.py --lawd-cd 11500 --deal-ym 202605
```

생성된 Markdown은 기본적으로 `output/` 아래에 저장됩니다.

## 환경 변수

`.env.example`을 복사해 `.env`를 만들고 필요한 값만 채웁니다.

```env
PUBLIC_DATA_API_KEY=
KAKAO_REST_API_KEY=
COMMERCIAL_DISTRICT_ENDPOINT=https://apis.data.go.kr/B553077/api/open/sdsc2/storeListInRadius
NEIS_API_KEY=
SEOUL_OPEN_DATA_KEY=
REB_API_KEY=
REB_STATBL_ID=
REB_CYCLE=MM
EXIM_API_KEY=
ECOS_API_KEY=
KIS_APP_KEY=
KIS_APP_SECRET=
KIS_BASE_URL=https://openapi.koreainvestment.com:9443
NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=
WORDPRESS_URL=
WORDPRESS_USERNAME=
WORDPRESS_APP_PASSWORD=
DEFAULT_STATUS=draft
DATABASE_PATH=data/app.db
LLM_API_KEY=
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1
```

필수 값은 실행하는 기능에 따라 다릅니다. 예를 들어 매매 실거래가만 수집하려면 `PUBLIC_DATA_API_KEY`가 필요하고, WordPress 발행에는 `WORDPRESS_URL`, `WORDPRESS_USERNAME`, `WORDPRESS_APP_PASSWORD`가 필요합니다.

## 월간 아파트 리포트

실거래가를 수집합니다.

```powershell
python scripts/collect_daily.py --lawd-cd 11500 --deal-ym 202605
```

DB에 저장된 데이터로 월간 리포트를 생성합니다.

```powershell
python scripts/generate_post.py --lawd-cd 11500 --deal-ym 202605
```

월간 리포트, 상승률 리포트, 거래량 1위 단지 상세 리포트를 한 번에 생성하려면 `--all`을 붙입니다.

```powershell
python scripts/generate_post.py --lawd-cd 11500 --deal-ym 202605 --all
```

LLM으로 문장을 다듬거나 대표 이미지를 만들 수 있습니다.

```powershell
python scripts/generate_post.py --lawd-cd 11500 --deal-ym 202605 --all --use-llm --generate-image
```

## 시장 브리프 데이터 수집

매매, 전월세, REB 통계, 법정동 코드 데이터를 함께 수집하고 시장 브리프 Markdown을 생성합니다.

```powershell
python scripts/collect_market_data.py --lawd-cd 11500 --deal-ym 202605
```

선택적으로 법정동 코드 검색, REB 통계표 ID, 추가 파라미터를 지정할 수 있습니다.

```powershell
python scripts/collect_market_data.py `
  --lawd-cd 11500 `
  --deal-ym 202605 `
  --region-keyword "서울특별시 강서구" `
  --reb-statbl-id "A_TEST" `
  --reb-param "ITM_ID=100001"
```

## 외부 지표 수집

거시 지표, 시세, 검색 트렌드는 `scripts/collect_external_data.py`의 하위 명령으로 수집합니다.

```powershell
python scripts/collect_external_data.py exim-exchange --search-date 20260609
python scripts/collect_external_data.py ecos --stat-code 731Y001 --cycle D --start-period 20260601 --end-period 20260609
python scripts/collect_external_data.py kis-quote --symbol 005930
python scripts/collect_external_data.py naver-trend --start-date 2026-06-01 --end-date 2026-06-09 --group "아파트=아파트,전세"
```

## 단지 생활권 리포트

특정 아파트의 거래 흐름, 주변 편의시설, 학교, 지하철, 상권 변화를 조합해 생활권 리포트를 생성합니다.

```powershell
python scripts/generate_apartment_living_report.py `
  --apartment "마곡엠밸리7단지" `
  --lawd-cd 11500 `
  --deal-ym 202605
```

실거래가를 먼저 수집한 뒤 생성하려면 `--collect-trades`를 붙입니다.

```powershell
python scripts/generate_apartment_living_report.py `
  --apartment "마곡엠밸리7단지" `
  --lawd-cd 11500 `
  --deal-ym 202605 `
  --collect-trades
```

카카오 로컬 API를 사용할 수 없거나 좌표를 직접 지정하고 싶을 때는 주소, 좌표, 가까운 역 정보를 수동으로 넘길 수 있습니다.

```powershell
python scripts/generate_apartment_living_report.py `
  --apartment "마곡엠밸리7단지" `
  --lawd-cd 11500 `
  --deal-ym 202605 `
  --address "서울특별시 강서구 마곡동" `
  --longitude 126.827 `
  --latitude 37.566 `
  --station-name "마곡나루" `
  --station-distance 500
```

## 배치 실행

기본 등록 지역 전체를 대상으로 수집, 분석, Markdown 생성을 한 번에 실행합니다.

```powershell
python scripts/run_batch.py --deal-ym 202605
```

이미 DB에 저장된 데이터만 사용하려면 수집을 건너뜁니다.

```powershell
python scripts/run_batch.py --deal-ym 202605 --skip-collect
```

특정 지역만 실행할 수도 있습니다. `--lawd-cd`는 여러 번 지정할 수 있습니다.

```powershell
python scripts/run_batch.py --deal-ym 202605 --lawd-cd 11500 --lawd-cd 11470
```

## WordPress 발행

생성된 Markdown 파일을 WordPress 글로 발행합니다. 기본 상태는 `.env`의 `DEFAULT_STATUS`를 따르며, 보통 `draft`로 둡니다.

```powershell
python scripts/publish_to_wordpress.py --file output/202605_11500_monthly_report.md
```

카테고리, 태그, 슬러그, 발췌문, 대표 이미지를 함께 지정할 수 있습니다.

```powershell
python scripts/publish_to_wordpress.py `
  --file output/202605_11500_monthly_report.md `
  --category 12 `
  --tag-name "실거래가" `
  --slug "gangseo-apartment-202605" `
  --excerpt "2026년 5월 강서구 아파트 실거래가 요약" `
  --featured-image output/images/202605_11500_featured.png
```

배치 실행과 발행을 한 번에 처리할 수도 있습니다.

```powershell
python scripts/run_batch.py --deal-ym 202605 --publish --use-llm --generate-image
```

## GitHub Actions

`.github/workflows/monthly-report.yml`은 매월 1일, 5일, 10일, 15일 21:00 UTC에 실행됩니다. 저장소 Secrets에 아래 값을 등록하면 자동으로 리포트를 생성하고 WordPress 초안으로 발행합니다.

- `PUBLIC_DATA_API_KEY`
- `WORDPRESS_URL`
- `WORDPRESS_USERNAME`
- `WORDPRESS_APP_PASSWORD`

수동 실행 시 `deal_ym` 입력값으로 대상 계약월을 지정할 수 있습니다.

## Markdown 품질 검사

생성된 리포트는 발행 전에 한글 깨짐, 미렌더링 템플릿, 제목 누락, 표 컬럼 불일치, 빈 링크 등을 검사합니다.
`generate_post.py`, `run_batch.py`, `publish_to_wordpress.py`는 기본적으로 audit을 실행하고, 오류가 있으면 발행을 중단합니다.

```powershell
python scripts/audit_markdown.py output/202605_11500_monthly_report.md
```

긴급히 기존 파일을 그대로 처리해야 하는 경우에는 `--skip-audit`을 사용할 수 있습니다.

## 테스트

```powershell
python -m unittest discover -s tests
```

테스트는 XML/JSON 파서, 분석 로직, Markdown 렌더링, WordPress 발행 fallback 등을 검증합니다.

## 디렉터리 구조

```text
app/
  analyzers/     # 거래/생활권 분석 로직
  collectors/    # 공공데이터 및 외부 API 수집기
  db/            # SQLite 스키마와 저장 함수
  generators/    # Markdown, LLM rewrite, 이미지 생성
  publishers/    # WordPress 발행
  services/      # 생활권 리포트 조립 서비스
scripts/         # CLI 실행 스크립트
templates/       # Jinja2 Markdown 템플릿
docs/            # API 연결 안내
tests/           # unittest 테스트
data/            # SQLite DB 저장 위치
output/          # 생성된 Markdown/이미지
assets/          # 기사 이미지와 캡처 자료
```

## 기본 지역 코드

현재 기본 배치 대상은 `app/config.py`의 `REGIONS`에 정의되어 있습니다.

| 지역 | 법정동코드 앞 5자리 |
| --- | ---: |
| 서울 강서구 | 11500 |
| 서울 양천구 | 11470 |
| 서울 마포구 | 11440 |
| 서울 영등포구 | 11560 |
| 서울 관악구 | 11620 |
| 서울 강동구 | 11740 |

## 데이터 주의사항

이 프로젝트의 리포트는 신고 기반 실거래가와 외부 API 응답을 바탕으로 생성됩니다. 거래 취소, 정정, API 지연, 좌표 보정, 상호 변경 등에 따라 결과가 달라질 수 있습니다. 생성된 글은 투자 권유가 아니라 콘텐츠 제작과 시장 점검을 위한 참고 자료로 사용해야 합니다.
