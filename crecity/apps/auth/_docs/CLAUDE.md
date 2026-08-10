# CLAUDE.md — auth (스포크)

회원 인증·계정 도메인. 토큰 발급 시크릿은 `.env.auth` 경계를 따른다
(`load_auth_env()` 명시 호출 — social_login_provider가 담당).

## 현재 슬라이스

| 슬라이스 | 엔드포인트 | 설명 |
|---|---|---|
| gatekeeper (myself) | `GET /auth/myself` | 자기소개 |
| social_login | `GET /auth/social/{provider}/authorize-url` · `POST /auth/social/{provider}/login` | 카카오·네이버·구글 OAuth. 프론트가 콜백 code를 login에 전달 → 가입(첫 로그인) 또는 로그인 → JWT(HS256, 30분) + 리프레시 토큰(Redis, 14일) 발급 |
| token_refresh | `POST /auth/tokens/refresh` | 리프레시 토큰 회전(1회용) — 소비 후 새 쌍 발급, 재사용 401 |

- 엔티티: `User`(+`AccountType` CREATOR/BRAND) · `SocialIdentity`(+`SocialProvider` KAKAO/NAVER/GOOGLE).
- 계정 배타성: `users.email` unique + 계정당 단일 `account_type` — 같은 이메일이면
  제공자가 달라도 기존 계정에 연결되고 유형은 최초 가입 시 결정(collabstr-analysis §3.8).
- 리프레시 토큰은 Redis(`auth:refresh:<sha256>`) — 원문 미저장, GETDEL 회전.
- OAuth 클라이언트 키는 `.env`(`KAKAO/NAVER/GOOGLE_CLIENT_ID/SECRET`) — 미설정이면
  서버는 뜨되 해당 제공자 로그인만 실패.
- **카카오는 보류 상태(2026-08-10)**: `account_email` 동의항목이 비즈 앱 전용이라
  전환 전에는 이메일을 못 받는다(로그인 시 400 정상 동작 확인). 구글·네이버는 실계정
  E2E 검증 완료. 런칭 전 비즈 앱 전환 후 동의항목만 켜면 코드 변경 없이 활성화된다.
- 예정: JWT 검증(허브 포트 경유 — creator 소유권 검증에 사용) · RBAC · 로그아웃(리프레시 폐기).
