# Real Estate Report Bot

서울 주요 구의 아파트 매매 실거래가를 공공데이터 API에서 수집하고, SQLite에 저장한 뒤 월간 분석 리포트를 Markdown으로 생성하는 MVP입니다. WordPress REST API draft 발행까지 지원합니다.

## 주요 기능

- 국토교통부 아파트 매매 실거래가 API 수집
- SQLite 저장 및 중복 저장 방지
- 월간 거래량, 평균 거래가, 평당가, 거래량 TOP 10, 상승률 TOP 10 분석
- Jinja2 기반 Markdown 블로그 글 생성
- WordPress REST API draft 생성
- API 키 없이도 동작 확인 가능한 샘플 데이터 로딩

## 빠른 시작

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

샘플 데이터로 리포트를 생성하려면:

```powershell
python scripts/load_sample_data.py
python scripts/generate_post.py --lawd-cd 11500 --deal-ym 202605
```

월간 리포트, 상승률 리포트, 거래량 1위 단지 상세 리포트를 한 번에 생성하려면:

```powershell
python scripts/generate_post.py --lawd-cd 11500 --deal-ym 202605 --all
```

공공데이터 API로 실제 데이터를 수집하려면 `.env`에 `PUBLIC_DATA_API_KEY`를 넣은 뒤:

```powershell
python scripts/collect_daily.py --lawd-cd 11500 --deal-ym 202605
python scripts/generate_post.py --lawd-cd 11500 --deal-ym 202605
```

여러 지역을 배치로 처리하려면:

```powershell
python scripts/run_batch.py --deal-ym 202605
```

이미 DB에 저장된 데이터만으로 배치 리포트를 만들려면:

```powershell
python scripts/run_batch.py --deal-ym 202605 --skip-collect
```

생성한 글을 WordPress draft로 바로 등록하려면:

```powershell
python scripts/run_batch.py --deal-ym 202605 --publish
```

GitHub Actions 자동 실행은 `.github/workflows/monthly-report.yml`에 포함되어 있습니다. 저장소 Secrets에 `PUBLIC_DATA_API_KEY`, `WORDPRESS_URL`, `WORDPRESS_USERNAME`, `WORDPRESS_APP_PASSWORD`를 등록하면 매월 1일, 5일, 10일, 15일 UTC 21시에 실행됩니다.

WordPress에 draft로 발행하려면:

```powershell
python scripts/publish_to_wordpress.py --file output/202605_11500_monthly_report.md
```

## 환경 변수

```env
PUBLIC_DATA_API_KEY=
WORDPRESS_URL=
WORDPRESS_USERNAME=
WORDPRESS_APP_PASSWORD=
DEFAULT_STATUS=draft
DATABASE_PATH=data/app.db
```

## MVP 대상 지역

| 지역 | 법정동코드 앞 5자리 |
|---|---:|
| 서울 강서구 | 11500 |
| 서울 양천구 | 11470 |
| 서울 마포구 | 11440 |
| 서울 영등포구 | 11560 |
| 서울 관악구 | 11620 |

## 데이터 주의사항

이 프로젝트는 신고 기반 실거래가 데이터를 사용합니다. 거래 신고, 정정, 해제 등에 따라 수치가 바뀔 수 있으며, 리포트는 투자 권유가 아닌 참고 자료로 작성됩니다.
