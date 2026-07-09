# {{ report.apartment_name }} 실거주 분석: 교통·학군·생활 인프라 총정리

{{ report.apartment_name }}를 실거주 관점에서 살펴봤습니다. 국토교통부 실거래 자료와 단지 반경 {{ report.radius_m }}m 생활시설, 학교, 상가업소, 대중교통 데이터를 한 리포트에 모았습니다.

- 위치: {{ report.address or "주소 정보 없음" }}
- 생활 인프라 기준일: {{ report.snapshot_date }}
- 실거래 기준월: {{ report.trade.deal_ym[:4] }}년 {{ report.trade.deal_ym[4:]|int }}월

## 한눈에 보는 결과

| 항목 | 점수 |
| --- | ---: |
| 교통 | {{ report.scores.transport }}점 |
| 생활편의 | {{ report.scores.convenience }}점 |
| 학군 | {{ report.scores.school }}점 |
| 의료 | {{ report.scores.medical }}점 |
| 상권활성도 | {{ report.scores.commercial }}점 |
| **종합** | **{{ report.scores.overall }}점** |

점수는 시설 수, 거리, 지하철 이용량, 상가 밀도와 업종 다양성을 같은 기준으로 환산한 상대 지표입니다. 주택의 품질이나 개인별 선호를 모두 반영하는 절대평가는 아닙니다.

## ① 실거래가와 단지 가치

| 항목 | 결과 |
| --- | ---: |
| 최근 거래량 | {{ report.trade.trade_count }}건 |
| 평균 거래가 | {{ report.trade.avg_deal_amount|money }} |
| 평균 평당가 | {{ report.trade.avg_price_per_pyeong|money }} |
| 전월 대비 평균가 | {{ report.trade.price_change_rate|percent }} |

거래가 없는 달은 평균 가격과 상승률을 계산하지 않았습니다. 같은 단지라도 면적, 층, 동, 내부 상태에 따라 실제 가격 차이가 큽니다.

## ② 교통

{% if report.transit.station_name %}
가장 가까운 지하철역은 **{{ report.transit.station_name }}**입니다. 단지 중심에서 {{ report.transit.distance_m|distance }}, 일반적인 보행 속도로 {{ report.transit.distance_m|walk }} 정도입니다.

{% if report.transit.daily_passengers is not none %}
- 노선: {{ report.transit.line_name or "노선 정보 없음" }}
- 승하차 기준일: {{ report.transit.use_date }}
- 일 승하차 합계: {{ report.transit.daily_passengers|number }}명
{% else %}
역 거리는 확인했지만 해당 날짜의 승하차 인원은 연결되지 않았습니다.
{% endif %}
{% else %}
반경 {{ report.radius_m }}m 안에서 지하철역을 확인하지 못했습니다.
{% endif %}

## ③ 생활편의시설

반경 {{ report.radius_m }}m 기준 카카오 로컬 검색 결과입니다.

| 시설 | 개수 |
| --- | ---: |
| 편의점 | {{ report.facilities.convenience_stores }}개 |
| 카페 | {{ report.facilities.cafes }}개 |
| 음식점 | {{ report.facilities.restaurants }}개 |
| 대형마트 | {{ report.facilities.large_marts }}개 |
| 공원 검색 결과 | {{ report.facilities.parks }}개 |
| 스타벅스 | {{ report.facilities.starbucks }}개 |
| 치킨 매장 검색 결과 | {{ report.facilities.chicken_shops }}개 |

카카오 검색의 `total_count`를 사용하므로 실제 영업 여부, 중복 지점, 복합시설 내부 매장에 따라 현장 체감과 차이가 날 수 있습니다.

## ④ 의료와 학원

| 시설 | 개수 |
| --- | ---: |
| 병원 | {{ report.facilities.hospitals }}개 |
| 약국 | {{ report.facilities.pharmacies }}개 |
| 학원 | {{ report.facilities.academies }}개 |

병원 수에는 의원급 의료기관이 함께 포함될 수 있습니다. 응급실, 소아과, 야간 진료처럼 필요한 진료과가 있는지는 별도로 확인해야 합니다.

## ⑤ 학군

반경 안에서 확인된 학교는 총 {{ report.schools.total_count }}곳입니다.

| 구분 | 가장 가까운 학교 | 거리 | 도보 환산 |
| --- | --- | ---: | ---: |
| 초등학교 | {{ report.schools.elementary.name if report.schools.elementary else "확인되지 않음" }} | {{ (report.schools.elementary.distance_m if report.schools.elementary else none)|distance }} | {{ (report.schools.elementary.distance_m if report.schools.elementary else none)|walk }} |
| 중학교 | {{ report.schools.middle.name if report.schools.middle else "확인되지 않음" }} | {{ (report.schools.middle.distance_m if report.schools.middle else none)|distance }} | {{ (report.schools.middle.distance_m if report.schools.middle else none)|walk }} |
| 고등학교 | {{ report.schools.high.name if report.schools.high else "확인되지 않음" }} | {{ (report.schools.high.distance_m if report.schools.high else none)|distance }} | {{ (report.schools.high.distance_m if report.schools.high else none)|walk }} |

학교 거리는 직선거리입니다. 실제 통학구역과 배정 학교, 횡단보도와 출입구를 반영한 통학 동선은 교육청 자료와 현장 경로를 함께 확인해야 합니다.

## ⑥ 상권 활성도

{% if report.commercial.total_stores is not none %}
반경 안의 상가업소는 {{ report.commercial.total_stores }}곳, 대분류 업종은 {{ report.commercial.category_count }}개로 집계됐습니다.

| 주요 업종 | 업소 수 |
| --- | ---: |
{% for item in report.commercial.top_categories %}
| {{ item.name }} | {{ item.count }}개 |
{% endfor %}

{% if report.commercial.previous_snapshot_date %}
이전 스냅샷({{ report.commercial.previous_snapshot_date }})과 비교하면 새로 포착된 업소는 {{ report.commercial.new_store_count }}곳, 사라진 업소는 {{ report.commercial.closed_store_count }}곳, 순변화는 {{ "%+d"|format(report.commercial.net_change) }}곳입니다.

이는 사업자 개·폐업 신고일을 직접 조회한 값이 아니라 두 시점의 상가업소 목록 차이입니다. 데이터 정정이나 상호 변경도 포함될 수 있어 **개업·폐업 추정치**로 봐야 합니다.
{% else %}
이번 실행은 첫 스냅샷이어서 개업·폐업 추정치를 만들지 않았습니다. 다음 수집부터 같은 단지·반경의 업소 목록 차이를 비교할 수 있습니다.
{% endif %}
{% else %}
상가업소 API 자료가 없어 상권 밀도와 스냅샷 변화는 중립값으로 계산했습니다.
{% endif %}

## ⑦ 실거주 유형별 평가

| 유형 | 평가 |
| --- | --- |
| 신혼부부 | {{ report.ratings.newlywed|stars }} |
| 1인 가구 | {{ report.ratings.single_household|stars }} |
| 자녀 가구 | {{ report.ratings.family|stars }} |
| 투자 관점 | {{ report.ratings.investment|stars }} |

별점은 위 점수의 조합입니다. 투자 관점에는 당월 거래량과 전월 대비 가격 흐름을 함께 반영했지만, 매수·매도 추천을 뜻하지 않습니다.

## 데이터 확인 사항

{% if report.warnings %}
{% for warning in report.warnings %}
- {{ warning }}
{% endfor %}
{% else %}
- 설정된 모든 API가 정상적으로 반영됐습니다.
{% endif %}

이 글은 공개 API를 자동 집계한 참고용 리포트입니다. 실거래 신고 정정, API 갱신 시차, 좌표 검색 오차가 있을 수 있습니다.
