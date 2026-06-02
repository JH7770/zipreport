# {{ report.deal_ym|ym }} {{ item.apartment_name }} 실거래가 요약

{{ report.region_name }} {{ item.dong or "" }}의 {{ item.apartment_name }} {{ item.exclusive_area_group or "" }} 거래를 정리했습니다.

## 거래 요약

- 거래 건수: {{ item.trade_count }}건
- 평균 거래가: {{ item.avg_deal_amount|money }}
- 최저 거래가: {{ item.min_deal_amount|money }}
- 최고 거래가: {{ item.max_deal_amount|money }}
- 평균 평당가: {{ item.avg_price_per_pyeong|money }}
- 전월 평균 거래가: {{ item.prev_avg_deal_amount|money }}
- 전월 대비 변화율: {{ item.price_change_rate|percent }}

## 참고 사항

같은 단지라도 층, 향, 동, 수리 상태, 거래 시점에 따라 가격 차이가 발생할 수 있습니다. 이 글은 공공데이터를 정리한 참고 자료이며 매수 또는 매도 추천이 아닙니다.
