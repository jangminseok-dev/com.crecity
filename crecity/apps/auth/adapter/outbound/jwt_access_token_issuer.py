from datetime import datetime, timedelta, timezone

import jwt

from auth.app.ports.output.access_token_issuer import AccessTokenIssuer
from auth.domain.entities.user_entity import User


class JwtAccessTokenIssuer(AccessTokenIssuer):
    """HS256 JWT 발급 — 서명 시크릿은 `.env.auth` 경계를 따른다(auth 분리 시 비대칭키 전환)."""

    def __init__(self, secret: str, ttl_seconds: int) -> None:
        self._secret = secret
        self._ttl_seconds = ttl_seconds

    def issue(self, user: User) -> str:
        now = datetime.now(timezone.utc)
        return jwt.encode(
            {
                "sub": str(user.id),
                "email": user.email,
                "account_type": user.account_type.value,
                "iat": now,
                "exp": now + timedelta(seconds=self._ttl_seconds),
            },
            self._secret,
            algorithm="HS256",
        )
