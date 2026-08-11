from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.adapter.outbound.mappers.social_identity_mapper import SocialIdentityMapper
from auth.adapter.outbound.orm.social_identity_orm import SocialIdentityOrm
from auth.app.ports.output.social_identity_repository import SocialIdentityRepository
from auth.domain.entities.social_identity_entity import SocialIdentity, SocialProvider


class SocialIdentityPgRepository(SocialIdentityRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, user_id: int, provider: SocialProvider, provider_user_id: str
    ) -> SocialIdentity:
        result = await self._session.execute(
            insert(SocialIdentityOrm)
            .values(user_id=user_id, provider=provider.value, provider_user_id=provider_user_id)
            .returning(SocialIdentityOrm)
        )
        await self._session.commit()
        return SocialIdentityMapper.to_entity(result.scalar_one())

    async def find_by_provider_uid(
        self, provider: SocialProvider, provider_user_id: str
    ) -> SocialIdentity | None:
        result = await self._session.execute(
            select(SocialIdentityOrm).where(
                SocialIdentityOrm.provider == provider.value,
                SocialIdentityOrm.provider_user_id == provider_user_id,
            )
        )
        orm = result.scalar_one_or_none()
        return SocialIdentityMapper.to_entity(orm) if orm is not None else None

    async def delete_by_user_id(self, user_id: int) -> None:
        await self._session.execute(
            delete(SocialIdentityOrm).where(SocialIdentityOrm.user_id == user_id)
        )
        await self._session.commit()
