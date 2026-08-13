# CLAUDE.md — admin (스포크)

플랫폼 운영 도메인 — 허브 포트 소비형(자체 테이블은 감사 로그뿐).
**전 기능 RBAC 보호** — `require_permission("<코드>")` 허브 DI 경유(403).

## 현재 슬라이스

| 슬라이스 | 엔드포인트 | 권한 | 설명 |
|---|---|---|---|
| audit_log_lookup | `GET /admin/audit-logs` | `profile.review` | 운영 감사 로그 조회(갭 #36) — 최신순 200건, append-only |
| steward (myself) | `GET /admin/myself` | — | 자기소개 |
| profile_review | `GET /admin/profiles/pending` · `POST /admin/profiles/{id}/approve·reject` | `profile.review` | 심사 대기 목록(오래된 순)·승인/반려. **정량 vetting 자동 체크 동봉**(갭 #16 — 채널 지표 등록·팔로워 합계·최고 참여율이 `VETTING_MIN_*` 기준을 넘는지. 자가입력 지표라 참고선일 뿐 자동 승인·반려는 하지 않는다). 상태 소유자는 creator — 허브 `ProfileReviewPort` 경유 전이. 심사자·결정은 감사 로그에 영속 기록 |
| dispute_resolution | `GET /admin/disputes/open` · `POST /admin/disputes/{id}/refund·release·dismiss` | `dispute.resolve` | 분쟁 중재(갭 #4) — 대기 목록(오래된 순, 주문 금액·당사자 포함)·판정. 환불=브랜드 전액 크레딧+주문 취소, 지급=크리에이터 적립+구매 확정, 기각=주문 유지. **부분 배분 없음.** 상태 소유자는 order — 허브 `DisputeResolutionPort` 경유(주문 전이·원장과 단일 트랜잭션). 판정자·결정은 감사 로그에 영속 기록 |
| withdrawal_settlement | `GET /admin/withdrawals/pending` · `GET /admin/withdrawals/annual-summary/{year}` · `POST /admin/withdrawals/{id}/complete·fail` | `withdrawal.settle` | 인출 운영 처리 + **연간 지급 집계**(갭 #2 — 지급명세서 제출 자료, 크리에이터별 합계·지급액 큰 순). — 운영자가 은행 이체 후 완료(PAID)/실패(FAILED·잔액 복원) 확정. 상태 소유자는 order — 허브 `WithdrawalSettlementPort` 경유. 처리자·결정은 감사 로그에 영속 기록 |

- 운영자 계정: `scripts/auth_grant_role.py <이메일> admin` — 화면·API로 역할 부여 불가.
- **감사 로그(갭 #36)**: `admin_audit_logs`(append-only) — 네 record 포트를 공용
  `PgAuditRecordAdapter`가 구현하며 `subject`로 종류를 구분한다. 기록 실패는 로그만
  남기고 통과시킨다(감사 기록이 심사·인출 처리·분쟁 판정을 되돌리지 않는다).
- 예정: 운영 대시보드.
