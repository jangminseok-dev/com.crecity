from __future__ import annotations

from fastapi import Depends, HTTPException, Header

from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.app.exceptions import InvalidAccessTokenError
from hub.app.ports.output.access_token_verifier_port import AccessTokenVerifier

# 조립 지점 — 허브는 스포크를 모르므로 main.py(조립 루트)가 auth 구현체를 등록한다.
_verifier: AccessTokenVerifier | None = None


def register_access_token_verifier(verifier: AccessTokenVerifier) -> None:
    global _verifier
    _verifier = verifier


def get_access_token_verifier() -> AccessTokenVerifier:
    if _verifier is None:
        raise RuntimeError(
            "AccessTokenVerifier 미등록 — main.py에서 register_access_token_verifier를 호출해야 합니다."
        )
    return _verifier


def get_current_user(
    authorization: str | None = Header(None, description="Bearer <액세스 토큰>"),
    verifier: AccessTokenVerifier = Depends(get_access_token_verifier),
) -> VerifiedUser:
    """보호 라우터 공용 의존성 — Bearer 토큰을 검증해 현재 사용자를 돌려준다(실패 시 401)."""
    if authorization is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다 — Authorization 헤더가 없습니다.")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Authorization 헤더는 'Bearer <토큰>' 형식이어야 합니다.")
    try:
        return verifier.verify(token)
    except InvalidAccessTokenError as error:
        raise HTTPException(status_code=401, detail=str(error))
