"""개발용 액세스 토큰 발급 — 소셜 로그인을 거치지 않고 API를 검증할 때 쓴다.

로그인이 필요한 경로(주문·답글·신고·운영 콘솔)를 사람이 브라우저로 들어가지 않고
확인하기 위한 도구다. **발급 로직은 만들지 않고 실제 서비스와 같은 발급기를 그대로 쓴다** —
따로 만들면 진짜 토큰과 다른 것을 검증하게 된다.

실행:
    cd crecity && PYTHONPATH=.:apps ../.venv/bin/python scripts/dev_issue_token.py <이메일>
    cd crecity && PYTHONPATH=.:apps ../.venv/bin/python scripts/dev_issue_token.py --list

로컬이 아닌 DB를 가리키면 실행을 거부한다(`--force`로만 넘길 수 있다). 운영 DB에서 돌리면
임의 계정의 토큰을 만들 수 있기 때문이다.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps"))

from sqlalchemy import select  # noqa: E402

from auth.adapter.outbound.jwt_access_token_issuer import JwtAccessTokenIssuer  # noqa: E402
from auth.adapter.outbound.orm.user_orm import UserOrm  # noqa: E402
from auth.adapter.outbound.pg.role_pg_repository import RolePgRepository  # noqa: E402
from auth.adapter.outbound.pg.user_pg_repository import UserPgRepository  # noqa: E402
from core.config import AUTH_ACCESS_TOKEN_TTL_SECONDS, DATABASE_URL  # noqa: E402
from core.database import dispose_engine, init_engine, session_scope  # noqa: E402
from core.key.secret_manager import get_secret_manager  # noqa: E402

_LOCAL_HOSTS = ("localhost", "127.0.0.1", "::1")


def _is_local_database() -> bool:
    """DATABASE_URL이 로컬을 가리키는지 — 운영 DB에서의 오발급을 막는 최소 가드."""
    return any(host in DATABASE_URL for host in _LOCAL_HOSTS)


async def _list_users() -> None:
    async with session_scope() as session:
        rows = await session.execute(
            select(UserOrm.id, UserOrm.email, UserOrm.name, UserOrm.account_type)
            .where(UserOrm.deleted_at.is_(None))
            .order_by(UserOrm.id)
        )
        print(f"{'id':>4}  {'유형':<8} {'이메일':<34} 이름")
        for user_id, email, name, account_type in rows.all():
            print(f"{user_id:>4}  {account_type:<8} {email:<34} {name}")


async def _issue(email: str) -> int:
    secrets = get_secret_manager()
    secrets.load_auth_env()  # 발급 시크릿은 `.env.auth` 경계
    issuer = JwtAccessTokenIssuer(
        secret=secrets.require("AUTH_JWT_SECRET"), ttl_seconds=AUTH_ACCESS_TOKEN_TTL_SECONDS
    )

    async with session_scope() as session:
        user = await UserPgRepository(session).find_by_email(email)
        if user is None:
            print(f"그런 이메일의 계정이 없습니다: {email}", file=sys.stderr)
            print("  → --list 로 목록을 확인하세요.", file=sys.stderr)
            return 1
        roles_repository = RolePgRepository(session)
        roles = await roles_repository.roles_for_user(user.id)
        permissions = await roles_repository.permissions_for_user(user.id)

    token = issuer.issue(user, roles, permissions)
    print(f"# {user.email} (id={user.id}, {user.account_type.value})")
    print(f"# 역할 {roles or '없음'} · 권한 {permissions or '없음'}")
    print(f"# 유효 {AUTH_ACCESS_TOKEN_TTL_SECONDS // 60}분")
    print(token)
    return 0


async def main() -> int:
    parser = argparse.ArgumentParser(description="개발용 액세스 토큰 발급")
    parser.add_argument("email", nargs="?", help="토큰을 발급할 계정 이메일")
    parser.add_argument("--list", action="store_true", help="계정 목록 보기")
    parser.add_argument("--force", action="store_true", help="로컬이 아닌 DB에서도 실행")
    args = parser.parse_args()

    if not _is_local_database() and not args.force:
        print("로컬 DB가 아닙니다 — 운영 DB에서는 토큰을 발급하지 않습니다.", file=sys.stderr)
        print("  정말 필요하면 --force 를 붙이세요.", file=sys.stderr)
        return 2
    if not args.list and not args.email:
        parser.print_help()
        return 2

    init_engine()
    try:
        if args.list:
            await _list_users()
            return 0
        return await _issue(args.email)
    finally:
        await dispose_engine()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
