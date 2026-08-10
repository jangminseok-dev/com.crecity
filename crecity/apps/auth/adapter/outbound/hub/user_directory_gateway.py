from __future__ import annotations

from auth.adapter.outbound.pg.user_pg_repository import UserPgRepository
from core.database import session_scope
from hub.app.dtos.user_ref_dto import UserRef
from hub.app.ports.output.user_directory_port import UserDirectoryPort


class UserDirectoryGateway(UserDirectoryPort):
    """허브 UserDirectoryPort 계약의 auth 구현 — main.py가 조립한다."""

    async def get_user(self, user_id: int) -> UserRef | None:
        async with session_scope() as session:
            user = await UserPgRepository(session).find_by_id(user_id)
        if user is None:
            return None
        return UserRef(user_id=user.id, name=user.name, account_type=user.account_type.value)
