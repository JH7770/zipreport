# 외부 시장 데이터 API 연결 가이드

이 프로젝트는 아래 외부 API를 `.env` 키로 연결합니다.

## 연결된 API와 필요한 키

| API | 용도 | `.env` 변수 |
| --- | --- | --- |
| 한국수출입은행 환율 API | 일별 환율 | `EXIM_API_KEY` |
| 한국은행 ECOS API | 기준금리, 환율, 물가 등 경제통계 | `ECOS_API_KEY` |
| 한국투자증권 KIS API | 국내 주식 현재가 시세 | `KIS_APP_KEY`, `KIS_APP_SECRET`, `KIS_BASE_URL` |
| 네이버 데이터랩 검색어트렌드 API | 키워드 검색 트렌드 | `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` |

기존 부동산 데이터 수집에는 아래 키도 계속 사용합니다.

| API | 용도 | `.env` 변수 |
| --- | --- | --- |
| 공공데이터포털 국토교통부/행정안전부 API | 아파트 거래, 전월세, 법정동 코드 | `PUBLIC_DATA_API_KEY` |
| 한국부동산원 R-ONE API | 부동산 통계 | `REB_API_KEY`, `REB_STATBL_ID`, `REB_CYCLE` |

## 키 발급 위치

### 한국수출입은행 환율 API

1. 한국수출입은행 Open API 페이지에서 환율 API를 신청합니다.
2. 발급된 인증키를 `.env`의 `EXIM_API_KEY`에 넣습니다.
3. API 요청은 `authkey`, `searchdate`, `data=AP01` 파라미터를 사용합니다.

### 한국은행 ECOS API

1. 한국은행 ECOS Open API에서 인증키를 발급받습니다.
2. 발급된 인증키를 `.env`의 `ECOS_API_KEY`에 넣습니다.
3. ECOS 통계코드는 ECOS 통계 조회 화면이나 Open API 통계목록에서 확인합니다.

### 한국투자증권 KIS API

1. 한국투자증권 계좌 개설 및 ID 연결 후 KIS Developers에서 Open API 서비스를 신청합니다.
2. 발급된 `App Key`, `App Secret`을 각각 `KIS_APP_KEY`, `KIS_APP_SECRET`에 넣습니다.
3. 실전투자 기본 REST URL은 `https://openapi.koreainvestment.com:9443`입니다.
4. 모의투자를 쓰는 경우 `KIS_BASE_URL=https://openapivts.koreainvestment.com:29443`로 바꿉니다.

### 네이버 데이터랩 검색어트렌드 API

1. NAVER Developers에서 애플리케이션을 등록합니다.
2. 사용 API로 `데이터랩(검색어트렌드)`를 선택합니다.
3. 발급된 Client ID와 Client Secret을 `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`에 넣습니다.

## `.env` 예시

```env
EXIM_API_KEY=
ECOS_API_KEY=
KIS_APP_KEY=
KIS_APP_SECRET=
KIS_BASE_URL=https://openapi.koreainvestment.com:9443
NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=
```

## 실행 예시

```powershell
python scripts/collect_external_data.py exim-exchange --search-date 20260609
```

```powershell
python scripts/collect_external_data.py ecos --stat-code 731Y001 --cycle D --start-period 20260601 --end-period 20260609 --item-code1 0000001
```

```powershell
python scripts/collect_external_data.py kis-quote --symbol 005930
```

```powershell
python scripts/collect_external_data.py naver-trend --start-date 2026-05-01 --end-date 2026-06-09 --time-unit date --group "강서구아파트=강서구 아파트,마곡 아파트"
```

수집 결과는 SQLite DB의 `exchange_rate`, `ecos_statistic`, `stock_quote`, `search_trend_point` 테이블에 저장됩니다.
