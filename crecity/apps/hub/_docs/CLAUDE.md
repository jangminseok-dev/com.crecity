# CLAUDE.md — hub (허브)

앱 간 협력의 단일 교차점. 계약(포트·DTO)만 소유하고 구체 스포크를 import하지 않는다.
현재 슬라이스: dispatcher(`GET /hub/myself`).
스포크가 소비할 포트는 `hub/app/ports/`에, DTO는 `hub/app/dtos/`에 둔다.

## 공개된 교차 협력 계약

| 계약 | 구성 | 구현 | 소비 |
|---|---|---|---|
| 현재 사용자 | `AccessTokenVerifier` 포트 + `VerifiedUser` DTO + `get_current_user` DI(`dependencies/current_user_provider.py`) | auth(`JwtAccessTokenVerifier`) — **main.py가 `register_access_token_verifier`로 조립** | creator 보호 라우터(`Depends(get_current_user)`, 실패 시 401) |

- 조립 규칙: 허브는 스포크를 모르므로 구현체 등록은 항상 main.py(조립 루트) 몫이다.
