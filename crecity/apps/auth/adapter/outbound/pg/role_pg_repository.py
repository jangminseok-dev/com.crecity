from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.adapter.outbound.orm.role_orm import (
    PermissionOrm,
    RoleOrm,
    RolePermissionOrm,
    UserRoleOrm,
)
from auth.app.ports.output.role_repository import RoleRepository


class RolePgRepository(RoleRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def permissions_for_user(self, user_id: int) -> list[str]:
        result = await self._session.execute(
            select(PermissionOrm.code)
            .join(RolePermissionOrm, RolePermissionOrm.permission_id == PermissionOrm.id)
            .join(UserRoleOrm, UserRoleOrm.role_id == RolePermissionOrm.role_id)
            .where(UserRoleOrm.user_id == user_id)
            .distinct()
            .order_by(PermissionOrm.code)
        )
        return list(result.scalars())

    async def roles_for_user(self, user_id: int) -> list[str]:
        result = await self._session.execute(
            select(RoleOrm.name)
            .join(UserRoleOrm, UserRoleOrm.role_id == RoleOrm.id)
            .where(UserRoleOrm.user_id == user_id)
            .order_by(RoleOrm.name)
        )
        return list(result.scalars())

    async def grant_role(self, user_id: int, role_name: str) -> bool:
        role_id = (
            await self._session.execute(select(RoleOrm.id).where(RoleOrm.name == role_name))
        ).scalar_one_or_none()
        if role_id is None:
            raise ValueError(f"존재하지 않는 역할입니다: {role_name}")
        exists = (
            await self._session.execute(
                select(UserRoleOrm.user_id).where(
                    UserRoleOrm.user_id == user_id, UserRoleOrm.role_id == role_id
                )
            )
        ).scalar_one_or_none()
        if exists is not None:
            return False
        await self._session.execute(insert(UserRoleOrm).values(user_id=user_id, role_id=role_id))
        await self._session.commit()
        return True
