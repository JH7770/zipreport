# {{ report.deal_ym|ym }} {{ report.region_name }} 아파트 상승률 TOP 10

{{ report.region_name }}에서 전월과 같은 단지·면적으로 비교 가능한 거래를 기준으로 상승률이 높은 단지를 정리했습니다.

| 순위 | 단지명 | 법정동 | 면적 | 전월 평균 | 이번 달 평균 | 변화율 |
|---:|---|---|---:|---:|---:|---:|
{% for item in report.top_rising_complexes %}
| {{ loop.index }} | {{ item.apartment_name }} | {{ item.dong or "-" }} | {{ item.exclusive_area_group or "-" }} | {{ item.prev_avg_deal_amount|money }} | {{ item.avg_deal_amount|money }} | {{ item.price_change_rate|percent }} |
{% else %}
| - | 전월과 직접 비교 가능한 단지가 부족합니다. | - | - | - | - | - |
{% endfor %}

## 해석 기준

상승률은 같은 단지명과 같은 전용면적 기준의 전월 평균 거래가 대비 이번 달 평균 거래가 변화율입니다. 거래가 1건뿐인 단지는 표본이 작으므로 참고 자료로만 보는 것이 좋습니다.

본 글은 투자 권유가 아닌 공공데이터 기반 참고 자료입니다.
