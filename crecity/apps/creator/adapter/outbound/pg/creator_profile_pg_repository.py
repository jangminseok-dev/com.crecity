from sqlalchemy import exists, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from creator.adapter.outbound.mappers.creator_profile_mapper import CreatorProfileMapper
from creator.adapter.outbound.orm.creator_profile_orm import CreatorProfileOrm
from creator.app.ports.output.creator_profile_repository import CreatorProfileRepository
from creator.domain.entities.creator_profile_entity import CreatorProfile, ProfileStatus


class CreatorProfilePgRepository(CreatorProfileRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        slug: str,
        name: str,
        tagline: str,
        bio: str,
        location: str | None,
        primary_category: str,
        status: ProfileStatus,
    ) -> CreatorProfile:
        result = await self._session.execute(
            insert(CreatorProfileOrm)
            .values(
                slug=slug,
                name=name,
                tagline=tagline,
                bio=bio,
                location=location,
                primary_category=primary_category,
                status=status.value,
            )
            .returning(CreatorProfileOrm)
        )
        await self._session.commit()
        return CreatorProfileMapper.to_entity(result.scalar_one())

    async def find_by_slug(self, slug: str) -> CreatorProfile | None:
        result = await self._session.execute(
            select(CreatorProfileOrm).where(CreatorProfileOrm.slug == slug)
        )
        orm = result.scalar_one_or_none()
        return CreatorProfileMapper.to_entity(orm) if orm is not None else None

    async def exists_by_slug(self, slug: str) -> bool:
        result = await self._session.execute(
            select(exists().where(CreatorProfileOrm.slug == slug))
        )
        return bool(result.scalar())

    async def list_by_status(
        self,
        status: ProfileStatus,
        category: str | None,
        limit: int,
        offset: int,
    ) -> list[CreatorProfile]:
        stmt = select(CreatorProfileOrm).where(CreatorProfileOrm.status == status.value)
        if category is not None:
            stmt = stmt.where(CreatorProfileOrm.primary_category == category)
        stmt = (
            stmt.order_by(CreatorProfileOrm.created_at.desc(), CreatorProfileOrm.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [CreatorProfileMapper.to_entity(orm) for orm in result.scalars()]

    async def count_by_status(self, status: ProfileStatus, category: str | None) -> int:
        stmt = (
            select(func.count())
            .select_from(CreatorProfileOrm)
            .where(CreatorProfileOrm.status == status.value)
        )
        if category is not None:
            stmt = stmt.where(CreatorProfileOrm.primary_category == category)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())
