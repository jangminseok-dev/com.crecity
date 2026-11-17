from __future__ import annotations

from auth.adapter.outbound.hub.jwt_access_token_verifier import JwtAccessTokenVerifier
from auth.adapter.outbound.redis.user_revocation_redis_store import UserRevocationRedisStore
from core.key.secret_manager import get_secret_manager


def build_access_token_verifier() -> JwtAccessTokenVerifier:
    """main.py 조립용 팩토리 — 발급과 같은 `.env.auth` 시크릿으로 검증기를 만든다."""
    secrets = get_secret_manager()
    secrets.load_auth_env()
    return JwtAccessTokenVerifier(
        secret=secrets.require("AUTH_JWT_SECRET"), revocations=UserRevocationRedisStore()
    )
