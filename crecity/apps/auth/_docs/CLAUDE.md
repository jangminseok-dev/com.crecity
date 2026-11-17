# CLAUDE.md — auth (스포크)

회원 인증·계정 도메인. 토큰 발급 시크릿은 `.env.auth` 경계를 따른다
(`load_auth_env()` 명시 호출 — social_login_provider가 담당).

## 현재 슬라이스

| 슬라이스 | 엔드포인트 | 설명 |
|---|---|---|
| gatekeeper (myself) | `GET /auth/myself` | 자기소개 |
| social_login | `GET /auth/social/{provider}/authorize-url` · `POST /auth/social/{provider}/login` | 카카오·네이버·구글 OAuth. 프론트가 콜백 code를 login에 전달 → 가입(첫 로그인) 또는 로그인 → JWT(HS256, 30분) + 리프레시 토큰(Redis, 14일) 발급 |
| token_refresh | `POST /auth/tokens/refresh` | 리프레시 토큰 회전(1회용) — 소비 후 새 쌍 발급, 재사용 401 |
| account_deletion | `POST /auth/account/delete` | 계정 탈퇴(§3.8, 갭 #33) — 허브 `ActiveOrderPort`·`CreditBalancePort`로 **활성 주문·잔액 검사(409)**, 통과 시 프로필 비활성화(`ProfileDeactivationPort`)·소셜 연결 해제·이메일 익명화 **소프트 삭제**(거래 기록 보존)·리프레시 토큰 폐기. 이미 발급된 액세스 토큰은 `UserRevocationStore`(Redis `auth:revoked-user:{id}`, 액세스 TTL과 같은 수명)에 올려 검증기가 거부한다 — 무상태 JWT라 TTL(30분)까지 살아 있던 문제를 2026-09-02 페르소나 여정에서 발견해 막았다 |
| logout | `POST /auth/tokens/logout` | 로그아웃 — 리프레시 토큰 즉시 폐기(Redis GETDEL). 없는 토큰도 멱등 204. BFF가 쿠키 삭제 전에 호출한다(갭 #5-1) |

- 엔티티: `User`(+`AccountType` CREATOR/BRAND) · `SocialIdentity`(+`SocialProvider` KAKAO/NAVER/GOOGLE).
- 계정 배타성: `users.email` unique + 계정당 단일 `account_type` — 같은 이메일이면
  제공자가 달라도 기존 계정에 연결되고 유형은 최초 가입 시 결정(collabstr-analysis §3.8).
- 리프레시 토큰은 Redis(`auth:refresh:<sha256>`) — 원문 미저장, GETDEL 회전.
- OAuth 클라이언트 키는 `.env`(`KAKAO/NAVER/GOOGLE_CLIENT_ID/SECRET`) — 미설정이면
  서버는 뜨되 해당 제공자 로그인만 실패.
- **카카오는 보류 상태(2026-08-10)**: `account_email` 동의항목이 비즈 앱 전용이라
  전환 전에는 이메일을 못 받는다(로그인 시 400 정상 동작 확인). 구글·네이버는 실계정
  E2E 검증 완료. 런칭 전 비즈 앱 전환 후 동의항목만 켜면 코드 변경 없이 활성화된다.
- JWT 검증은 허브 계약(`AccessTokenVerifier`)의 구현(`adapter/outbound/hub/`)으로 제공 —
  main.py가 조립하고 creator 등 스포크는 허브 `get_current_user`로 소비한다.

## RBAC (정통 — 2026-08-10 도입)

- 테이블 4종(3NF): `roles` · `permissions` · `role_permissions` · `user_roles`(복합 PK M:N).
  역할·권한 정의는 **마이그레이션 시드가 소유**(런타임 생성 없음). 권한 코드 규약
  `<도메인>.<행위>` (예: `profile.review`).
- 발급 시 `roles`·`permissions` 클레임 스냅샷(RolePgRepository 조회) → 검증은 토큰만으로.
  역할 변경은 토큰 재발급(액세스 TTL 30분) 시 반영 — 표준 트레이드오프.
- 인가 검사 단위는 **permission** — 스포크는 허브 `require_permission("코드")` DI로 보호(403).
- 역할 부여는 `scripts/auth_grant_role.py <이메일> <역할>` 스크립트로만(운영자 가입 플로우 없음).
- 시드: `admin` 역할 ← `profile.review`(프로필 심사). 새 권한은 마이그레이션으로 추가.
- 예정: 역할 관리 API(실수요 시). (로그아웃 리프레시 폐기는 2026-08-11 구축 완료)
