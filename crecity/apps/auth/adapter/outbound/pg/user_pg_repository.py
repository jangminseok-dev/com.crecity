from sqlalchemy import func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from auth.adapter.outbound.mappers.user_mapper import UserMapper
from auth.adapter.outbound.orm.user_orm import UserOrm
from auth.app.ports.output.user_repository import UserRepository
from auth.domain.entities.user_entity import AccountType, User


class UserPgRepository(UserRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, email: str, name: str, account_type: AccountType) -> User:
        result = await self._session.execute(
            insert(UserOrm)
            .values(email=email, name=name, account_type=account_type.value)
            .returning(UserOrm)
        )
        await self._session.commit()
        return UserMapper.to_entity(result.scalar_one())

    async def find_by_id(self, user_id: int) -> User | None:
        result = await self._session.execute(select(UserOrm).where(UserOrm.id == user_id))
        orm = result.scalar_one_or_none()
        return UserMapper.to_entity(orm) if orm is not None else None

    async def find_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(UserOrm).where(UserOrm.email == email))
        orm = result.scalar_one_or_none()
        return UserMapper.to_entity(orm) if orm is not None else None

    async def soft_delete(self, user_id: int, anonymized_email: str) -> None:
        await self._session.execute(
            update(UserOrm)
            .where(UserOrm.id == user_id)
            .values(email=anonymized_email, name="탈퇴한 사용자", deleted_at=func.now())
        )
        await self._session.commit()
