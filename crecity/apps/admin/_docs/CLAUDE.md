# CLAUDE.md — admin (스포크)

플랫폼 운영 도메인 — 허브 포트 소비형(자체 테이블 없음, 감사 로그는 로그 어댑터로 시작).
**전 기능 RBAC 보호** — `require_permission("<코드>")` 허브 DI 경유(403).

## 현재 슬라이스

| 슬라이스 | 엔드포인트 | 권한 | 설명 |
|---|---|---|---|
| steward (myself) | `GET /admin/myself` | — | 자기소개 |
| profile_review | `GET /admin/profiles/pending` · `POST /admin/profiles/{id}/approve·reject` | `profile.review` | 심사 대기 목록(오래된 순)·승인/반려. 상태 소유자는 creator — 허브 `ProfileReviewPort` 경유 전이. 심사자·결정은 감사 기록(로그) |
| withdrawal_settlement | `GET /admin/withdrawals/pending` · `POST /admin/withdrawals/{id}/complete·fail` | `withdrawal.settle` | 인출 운영 처리 — 운영자가 은행 이체 후 완료(PAID)/실패(FAILED·잔액 복원) 확정. 상태 소유자는 order — 허브 `WithdrawalSettlementPort` 경유. 처리자·결정은 감사 기록(로그) |

- 운영자 계정: `scripts/auth_grant_role.py <이메일> admin` — 화면·API로 역할 부여 불가.
- 예정: 분쟁 중재 · 운영 대시보드 · 감사 로그 영속화(PG 어댑터 교체).
