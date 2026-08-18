# CLAUDE.md — review (스포크)

거래 신뢰 도메인 — 3축 평점(소통·기한 준수·만족도, collabstr §2.1)과 리뷰 블러 정책(§2.3).

## 현재 슬라이스

| 슬라이스 | 엔드포인트 | 설명 |
|---|---|---|
| appraiser (myself) | `GET /review/myself` | 자기소개 |
| review_submission | `POST /review/orders/{id}/review` · `GET /review/orders/{id}/review` | **완료(COMPLETED) 주문의 브랜드만, 주문당 1회**(403/409). 3축 1~5점 + 본문. 주문 검증은 허브 `OrderParticipantsPort` 경유. 리뷰 저장과 **같은 트랜잭션**으로 `review.received`를 적재해 크리에이터에게 알린다(갭 #75) — 링크는 답글 폼이 있는 공개 프로필이라 슬러그를 `CreatorRefPort`로 해석하며, **프로필이 없으면 알림도 보내지 않는다** |
| review_listing | `GET /review/creators/{slug}` | 공개 조회 — **집계(3축 평균·종합·개수)는 항상 공개, 원문은 로그인 시에만**(비로그인 `comment=null`·`is_locked` — 가입 유도 장치). 슬러그 해석은 허브 `CreatorRefPort` 경유. 답글(`reply`·`replied_at`)은 **원문이 잠기면 함께 잠긴다**. `can_reply`는 보는 사람이 대상 크리에이터이고 아직 답글이 없을 때만 true — **크리에이터 user_id를 공개 응답에 노출하지 않으려고 서버가 판정한다** |
| review_reply | `POST /review/reviews/{id}/reply` | 크리에이터 답글(갭 #53) — **리뷰를 받은 크리에이터만(403), 리뷰당 1회(409)**, 1~1000자. 자격·중복 판정은 도메인 `Review.ensure_can_reply` |
| brand_review | `POST·GET /review/orders/{id}/brand-review` · `GET /review/brands/{user_id}/rating` | 양방향 평가(갭 #83) — **완료(COMPLETED) 주문의 크리에이터만, 주문당 1회(403/409)**. 단일 종합 평점(1~5)+코멘트(브랜드 축을 3축에 억지로 맞추지 않음). 집계(`/brands/{id}/rating`)는 **공개**(평점·건수만 — 크리에이터 평점 공개와 대칭), **코멘트 원문은 비공개**(보복 우려). 저장과 같은 트랜잭션으로 `review.brand_received` 적재(브랜드 알림). 화면: 주문 상세에 크리에이터용 평가 폼 + 크리에이터가 볼 때 상대 브랜드 평점 배지(0건이면 미표시 — 신규 브랜드 보호, #65 원칙) |

- 엔티티: `Review` — 종합 평점 = 3축 평균(도메인 `overall_score`), 범위 검증(`validate_score`).
- 테이블 `reviews` — order_id unique(주문당 1개), 타 스포크 id는 논리 참조(DB FK 없음).
- 평점·본문은 수정·삭제 없음(작성 전용). **답글도 한 번 남기면 되돌리지 않는다** — 평판
  기록이 사후에 흔들리지 않아야 한다는 같은 이유다. 신고·운영 중재는 예정.
- 답글은 리뷰에 1:1 종속이라 `reviews.reply`·`replied_at` 컬럼으로 둔다(별도 테이블 아님).
- 테이블 `brand_reviews`(갭 #83) — order_id unique(주문당 1개), 작성 전용·논리 참조 등
  `reviews`와 같은 원칙. 별도 테이블인 이유: 평가 축(단일 평점)과 공개 정책이 달라
  한 테이블에 섞으면 nullable 축이 늘어난다.
- 로그인 여부 분기는 허브 `get_optional_user`(무효 토큰=비로그인 취급).
