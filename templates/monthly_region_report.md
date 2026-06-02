# {{ report.deal_ym|ym }} {{ report.region_name }} 아파트 실거래가 리포트

{{ report.deal_ym|ym }} {{ report.region_name }} 아파트 매매 실거래는 총 {{ report.total_count }}건으로 집계되었습니다. 전월 {{ report.prev_total_count }}건과 비교하면 거래량 변화율은 {{ report.count_change_rate|percent }}입니다.

## 핵심 요약

- 총 거래 건수: {{ report.total_count }}건
- 전월 대비 거래량 변화: {{ report.count_change_rate|percent }}
- 평균 거래가: {{ report.avg_deal_amount|money }}
- 전월 평균 거래가: {{ report.prev_avg_deal_amount|money }}
- 평균 거래가 변화: {{ report.avg_change_rate|percent }}

## 거래량 TOP 10 단지

| 순위 | 단지명 | 법정동 | 면적 | 거래 건수 | 평균 거래가 | 평당가 |
|---:|---|---|---:|---:|---:|---:|
{% for item in report.top_volume_complexes %}
| {{ loop.index }} | {{ item.apartment_name }} | {{ item.dong or "-" }} | {{ item.exclusive_area_group or "-" }} | {{ item.trade_count }} | {{ item.avg_deal_amount|money }} | {{ item.avg_price_per_pyeong|money }} |
{% endfor %}

## 전월 대비 상승 단지

| 순위 | 단지명 | 법정동 | 면적 | 전월 평균 | 이번 달 평균 | 변화율 |
|---:|---|---|---:|---:|---:|---:|
{% for item in report.top_rising_complexes %}
| {{ loop.index }} | {{ item.apartment_name }} | {{ item.dong or "-" }} | {{ item.exclusive_area_group or "-" }} | {{ item.prev_avg_deal_amount|money }} | {{ item.avg_deal_amount|money }} | {{ item.price_change_rate|percent }} |
{% else %}
| - | 전월과 직접 비교 가능한 단지가 부족합니다. | - | - | - | - | - |
{% endfor %}

## 신고가 후보 단지

최근 집계 기준 최고 거래금액이 높은 단지입니다. 실제 신고가 여부는 해제 거래, 면적, 층, 이전 거래 이력에 따라 달라질 수 있습니다.

| 순위 | 단지명 | 법정동 | 면적 | 최고 거래가 | 최저 거래가 |
|---:|---|---|---:|---:|---:|
{% for item in report.record_high_complexes %}
| {{ loop.index }} | {{ item.apartment_name }} | {{ item.dong or "-" }} | {{ item.exclusive_area_group or "-" }} | {{ item.max_deal_amount|money }} | {{ item.min_deal_amount|money }} |
{% endfor %}

## 참고 사항

본 글은 국토교통부 공공데이터 API 기반의 신고 자료를 정리한 참고용 리포트입니다. 거래 신고와 정정, 해제 처리 시점에 따라 수치는 달라질 수 있으며, 매수 또는 매도 추천으로 해석해서는 안 됩니다.
