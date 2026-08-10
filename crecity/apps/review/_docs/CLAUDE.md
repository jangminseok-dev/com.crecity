# CLAUDE.md — review (스포크)

거래 신뢰 도메인 — 3축 평점(소통·기한 준수·만족도, collabstr §2.1)과 리뷰 블러 정책(§2.3).

## 현재 슬라이스

| 슬라이스 | 엔드포인트 | 설명 |
|---|---|---|
| appraiser (myself) | `GET /review/myself` | 자기소개 |
| review_submission | `POST /review/orders/{id}/review` · `GET /review/orders/{id}/review` | **완료(COMPLETED) 주문의 브랜드만, 주문당 1회**(403/409). 3축 1~5점 + 본문. 주문 검증은 허브 `OrderParticipantsPort` 경유 |
| review_listing | `GET /review/creators/{slug}` | 공개 조회 — **집계(3축 평균·종합·개수)는 항상 공개, 원문은 로그인 시에만**(비로그인 `comment=null`·`is_locked` — 가입 유도 장치). 슬러그 해석은 허브 `CreatorRefPort` 경유 |

- 엔티티: `Review` — 종합 평점 = 3축 평균(도메인 `overall_score`), 범위 검증(`validate_score`).
- 테이블 `reviews` — order_id unique(주문당 1개), 타 스포크 id는 논리 참조(DB FK 없음).
- 수정·삭제 없음(작성 전용) — 신고·운영 중재는 예정.
- 로그인 여부 분기는 허브 `get_optional_user`(무효 토큰=비로그인 취급).
