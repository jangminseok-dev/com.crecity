# CLAUDE.md — admin (스포크)

플랫폼 운영 도메인 — 대체로 허브 포트 소비형(자체 테이블은 감사 로그·신고).
**운영 기능은 RBAC 보호** — `require_permission("<코드>")` 허브 DI 경유(403).
**예외는 신고 접수 하나**(`POST /admin/reports`) — 어뷰징을 당한 당사자가 내는 창구라
로그인 사용자면 누구나 쓴다(열람·처리는 권한자만).

## 현재 슬라이스

| 슬라이스 | 엔드포인트 | 권한 | 설명 |
|---|---|---|---|
| audit_log_lookup | `GET /admin/audit-logs` | `profile.review` | 운영 감사 로그 조회(갭 #36) — 최신순 200건, append-only |
| report | `POST /admin/reports` · `GET /admin/reports/open` · `POST /admin/reports/{id}/resolve` | 접수=로그인 / 열람·처리=`report.review` | 어뷰징 신고(갭 #54) — **주문 밖** 문제를 받는 창구(주문 안 다툼은 order `dispute`). 대상은 `ReportTargetType`(PROFILE·CONVERSATION) + target_id **다형 논리 참조**(FK 없음). 사유 10~2000자(422), **같은 신고자·같은 대상에 대기 중 신고가 있으면 409**. 처리는 메모를 남기고 닫으며(재처리 409) 감사 로그에 `report_review`로 기록 |
| order_search | `GET /admin/orders` | `order.search` | 운영 주문 검색(갭 #56) — 문의 대응용 **읽기 전용**. `order_id`(정확 일치)·`status`·`user_id`(브랜드·크리에이터 어느 쪽이든) AND 조합, 최신순, `limit`≤50·`offset`, 응답은 `items`+`total`(같은 조건). 주문 소유자는 order — 허브 `OrderSearchPort` 경유. **상태 문자열은 order 어휘지만 enum을 import하지 않는다**(스포크 독립 — 잘못된 값은 결과 0건) |
| steward (myself) | `GET /admin/myself` | — | 자기소개 |
| dashboard_metrics | `GET /admin/dashboard/metrics` | `dashboard.view` | 운영 대시보드 지표(갭 #55) — 가입(auth)·심사 현황(creator)·주문 상태별 건수/거래액/수수료 수입/분쟁·인출 대기(order)를 한 응답으로. **세 스포크가 각자 자기 지표를 집계**하고(허브 `AccountMetricsPort`·`ProfileMetricsPort`·`OrderMetricsPort`) 인터랙터가 `asyncio.gather`로 합친다. 수수료 수입은 **원장 `PLATFORM_REVENUE` 합**(도메인 내림 계산을 SQL로 복제하지 않는다), 거래액은 COMPLETED 주문 금액 합. **새 테이블 없음**(조회 시점 스냅샷) |
| profile_review | `GET /admin/profiles/pending` · `POST /admin/profiles/{id}/approve·reject` | `profile.review` | 심사 대기 목록(오래된 순)·승인/반려. **반려는 사유(5~500자) 필수**(갭 #101 — body `reason`, 사유 없는 반려는 크리에이터가 보완할 수 없다. 사유는 프로필에 저장·알림 동봉·감사 로그 기록). **정량 vetting 자동 체크 동봉**(갭 #16 — 채널 지표 등록·팔로워 합계·최고 참여율이 `VETTING_MIN_*` 기준을 넘는지. 자가입력 지표라 참고선일 뿐 자동 승인·반려는 하지 않는다). 상태 소유자는 creator — 허브 `ProfileReviewPort` 경유 전이. 심사자·결정은 감사 로그에 영속 기록 |
| dispute_resolution | `GET /admin/disputes/open` · `POST /admin/disputes/{id}/refund·release·dismiss` | `dispute.resolve` | 분쟁 중재(갭 #4) — 대기 목록(오래된 순, 주문 금액·당사자 포함)·판정. 환불=브랜드 전액 크레딧+주문 취소, 지급=크리에이터 적립+구매 확정, 기각=주문 유지. **부분 배분 없음.** 상태 소유자는 order — 허브 `DisputeResolutionPort` 경유(주문 전이·원장과 단일 트랜잭션). 판정자·결정은 감사 로그에 영속 기록 |
| withdrawal_settlement | `GET /admin/withdrawals/pending` · `GET /admin/withdrawals/annual-summary/{year}` · `POST /admin/withdrawals/{id}/complete·fail` | `withdrawal.settle` | 인출 운영 처리 + **연간 지급 집계**(갭 #2 — 지급명세서 제출 자료, 크리에이터별 합계·지급액 큰 순). — 운영자가 은행 이체 후 완료(PAID)/실패(FAILED·잔액 복원) 확정. 상태 소유자는 order — 허브 `WithdrawalSettlementPort` 경유. 처리자·결정은 감사 로그에 영속 기록 |

- 운영자 계정: `scripts/auth_grant_role.py <이메일> admin` — 화면·API로 역할 부여 불가.
  운영 화면을 API로 확인할 때는 `scripts/dev_issue_token.py <이메일>`로 토큰을 얻는다.
- **감사 로그(갭 #36)**: `admin_audit_logs`(append-only) — 다섯 record 포트를 공용
  `PgAuditRecordAdapter`가 구현하며 `subject`로 종류를 구분한다. 기록 실패는 로그만
  남기고 통과시킨다(감사 기록이 심사·인출 처리·분쟁 판정·신고 처리를 되돌리지 않는다).
- **신고 처리는 조치가 아니다**: 이 슬라이스는 접수·판단 기록만 남긴다. 실제 조치(프로필
  반려·계정 정지 등)는 각 소유 스포크의 기능으로 따로 한다 — 신고 큐가 남의 상태를
  직접 바꾸면 스포크 경계가 무너진다.
- **지표 포트를 셋으로 쪼갠 이유**: 포트 하나를 여러 스포크가 구현할 수 없고, 하나로 묶으면
  허브가 특정 스포크를 알게 된다. 지표가 늘면 소유 스포크의 포트에 필드를 더한다.
- 데모 주문도 **정상 결제와 같은 원장을 남긴다**(2026-08-14 수정). `seed_demo_data.py`가
  주문 행만 넣던 시절에는 거래액 대비 수수료 수입이 낮게 보였다 — 지금은 도메인 전이
  (accept→submit→approve)를 그대로 태워 예치·적립·수수료가 실제와 같은 모양으로 쌓인다.
