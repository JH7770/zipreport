# 아파트 실거주 리포트 API 연결

`scripts/generate_apartment_living_report.py`는 실거래가, 주변 시설, 학교, 상가업소, 서울 지하철 승하차를 결합해 아파트 단위 Markdown 리포트를 만듭니다.

## 필요한 API 키

| 환경 변수 | API | 필수 여부 | 용도 |
| --- | --- | --- | --- |
| `KAKAO_REST_API_KEY` | 카카오 로컬 REST API | 필수 | 단지 좌표, 반경 시설, 학교와 지하철 거리 |
| `PUBLIC_DATA_API_KEY` | 공공데이터포털 | 선택 | 국토부 실거래 수집, 상가업소 반경 조회 |
| `NEIS_API_KEY` | 나이스 교육정보 개방 포털 | 선택 | 학교 유형과 주소 보강 |
| `SEOUL_OPEN_DATA_KEY` | 서울 열린데이터광장 | 선택 | 서울 지하철 일별 승하차 인원 |
| `COMMERCIAL_DISTRICT_ENDPOINT` | 상가업소 API URL | 선택 | 공공데이터포털 명세 변경 시 URL 교체 |

`.env` 예시:

```env
KAKAO_REST_API_KEY=
PUBLIC_DATA_API_KEY=
NEIS_API_KEY=
SEOUL_OPEN_DATA_KEY=
COMMERCIAL_DISTRICT_ENDPOINT=https://apis.data.go.kr/B553077/api/open/sdsc2/storeListInRadius
```

API 신청과 최신 명세는 아래 공식 문서에서 확인합니다.

- 카카오 로컬: https://developers.kakao.com/docs/latest/ko/local/dev-guide
- 상가(상권)정보 API: https://www.data.go.kr/data/15012005/openapi.do
- 나이스 교육정보 개방 포털: https://open.neis.go.kr/
- 서울 지하철 승하차 데이터: https://data.seoul.go.kr/dataList/OA-12914/S/1/datasetView.do

상가 API는 활용신청이 승인된 공공데이터 키가 필요합니다. 계정에 연결된 상세기능 URL이 기본값과 다르면 `COMMERCIAL_DISTRICT_ENDPOINT`만 바꾸면 됩니다.

## 실행

기존 DB의 실거래 자료를 사용해 리포트를 생성합니다.

```powershell
python scripts/generate_apartment_living_report.py `
  --apartment "마곡엠밸리7단지" `
  --lawd-cd 11500 `
  --deal-ym 202605
```

당월과 전월 국토부 실거래를 먼저 수집하려면 `--collect-trades`를 붙입니다.

```powershell
python scripts/generate_apartment_living_report.py `
  --apartment "마곡엠밸리7단지" `
  --lawd-cd 11500 `
  --deal-ym 202605 `
  --collect-trades
```

WordPress 초안까지 한 번에 만들 수 있습니다.

```powershell
python scripts/generate_apartment_living_report.py `
  --apartment "마곡엠밸리7단지" `
  --lawd-cd 11500 `
  --deal-ym 202605 `
  --use-llm `
  --publish
```

## 개업·폐업 수치 해석

상가업소 API의 현재 목록만으로 실제 개업일과 폐업일을 알 수는 없습니다. 이 프로젝트는 `commercial_store_snapshot` 테이블에 날짜별 업소 ID를 저장하고 이전 스냅샷과 비교합니다.

- 첫 실행: 기준선만 저장, 신규·이탈 수치 없음
- 다음 실행: 새로 나타난 업소를 신규 포착, 사라진 업소를 영업 종료 추정으로 표시
- 주의: 상호 변경, 데이터 정정, 좌표 수정도 변화에 포함될 수 있음

따라서 글에는 이 값을 신고 기반 개·폐업 통계가 아닌 스냅샷 비교 추정치로 표기합니다.
