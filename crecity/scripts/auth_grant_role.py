"""역할 부여 관리 스크립트 — 운영자 가입 플로우는 없다(RBAC 부여는 이 스크립트로만).

실행:
    cd crecity && PYTHONPATH=.:apps ../.venv/bin/python scripts/auth_grant_role.py <이메일> <역할>
예:
    PYTHONPATH=.:apps ../.venv/bin/python scripts/auth_grant_role.py user@example.com admin
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps"))

from core.database import dispose_engine, init_engine, session_scope  # noqa: E402
from auth.adapter.outbound.pg.role_pg_repository import RolePgRepository  # noqa: E402
from auth.adapter.outbound.pg.user_pg_repository import UserPgRepository  # noqa: E402


async def main(email: str, role_name: str) -> None:
    init_engine()
    try:
        async with session_scope() as session:
            user = await UserPgRepository(session).find_by_email(email)
            if user is None:
                print(f"사용자를 찾을 수 없습니다: {email}")
                return
            roles = RolePgRepository(session)
            granted = await roles.grant_role(user.id, role_name)
            print(
                f"{email} (user_id={user.id}) ← '{role_name}' "
                + ("부여 완료" if granted else "이미 부여됨")
            )
            print(f"현재 권한: {await roles.permissions_for_user(user.id)}")
            print("※ 이미 로그인된 세션은 토큰 재발급(최대 30분 내 자동) 후 반영됩니다.")
    finally:
        await dispose_engine()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    asyncio.run(main(sys.argv[1], sys.argv[2]))
