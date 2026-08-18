"""개발용 리프레시 토큰 발급 — 브라우저 E2E(scripts/e2e.py)가 로그인 세션을 만들 때 쓴다.

액세스 토큰(dev_issue_token.py)과 달리 리프레시 토큰은 httpOnly 쿠키로 심어
프론트의 실제 세션 복원 경로(POST /api/auth/refresh)를 그대로 태울 수 있다.
**발급 로직은 만들지 않는다** — 실제 서비스와 같은 생성 방식(secrets.token_urlsafe(48))과
같은 저장소(RefreshTokenRedisStore)를 그대로 쓴다. 토큰은 1회용(회전)이라 매 실행마다 새로 받는다.

실행:
    cd crecity && PYTHONPATH=.:apps ../.venv/bin/python scripts/dev_issue_refresh.py <이메일>

로컬이 아닌 DB를 가리키면 실행을 거부한다(`--force`로만 넘길 수 있다).
"""

from __future__ import annotations

import argparse
import asyncio
import os
import secrets
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps"))

from redis.asyncio import Redis  # noqa: E402
from sqlalchemy import select  # noqa: E402

from auth.adapter.outbound.orm.user_orm import UserOrm  # noqa: E402
from auth.adapter.outbound.redis.refresh_token_redis_store import (  # noqa: E402
    RefreshTokenRedisStore,
)
from core.config import (  # noqa: E402
    AUTH_REFRESH_TOKEN_TTL_SECONDS,
    DATABASE_URL,
    REDIS_URL,
)
from core.database import dispose_engine, init_engine, session_scope  # noqa: E402

_LOCAL_HOSTS = ("localhost", "127.0.0.1", "::1")


def _is_local_database() -> bool:
    return any(host in DATABASE_URL for host in _LOCAL_HOSTS)


async def _issue(email: str) -> int:
    async with session_scope() as session:
        row = await session.execute(
            select(UserOrm.id).where(UserOrm.email == email, UserOrm.deleted_at.is_(None))
        )
        user_id = row.scalar_one_or_none()
    if user_id is None:
        print(f"그런 이메일의 계정이 없습니다: {email}", file=sys.stderr)
        print("  → dev_issue_token.py --list 로 목록을 확인하세요.", file=sys.stderr)
        return 1

    redis = Redis.from_url(REDIS_URL)
    try:
        token = secrets.token_urlsafe(48)
        await RefreshTokenRedisStore(redis).save(token, user_id, AUTH_REFRESH_TOKEN_TTL_SECONDS)
    finally:
        await redis.aclose()
    print(token)
    return 0


async def main() -> int:
    parser = argparse.ArgumentParser(description="개발용 리프레시 토큰 발급")
    parser.add_argument("email", help="토큰을 발급할 계정 이메일")
    parser.add_argument("--force", action="store_true", help="로컬이 아닌 DB에서도 실행")
    args = parser.parse_args()

    if not _is_local_database() and not args.force:
        print("로컬 DB가 아닙니다 — 운영 DB에서는 토큰을 발급하지 않습니다.", file=sys.stderr)
        print("  정말 필요하면 --force 를 붙이세요.", file=sys.stderr)
        return 2

    init_engine()
    try:
        return await _issue(args.email)
    finally:
        await dispose_engine()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
