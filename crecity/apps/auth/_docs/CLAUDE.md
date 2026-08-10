# CLAUDE.md — auth (스포크)

회원 인증·계정 도메인. 현재 슬라이스: gatekeeper(`GET /auth/myself`).
예정: 소셜 로그인(카카오·네이버·구글) · JWT 발급/검증 · 크리에이터/브랜드 계정 배타성
(동일 이메일 겸용 불가 — collabstr-analysis §3.8). 토큰 발급 개인키는 `.env.auth` 경계를 따른다.
