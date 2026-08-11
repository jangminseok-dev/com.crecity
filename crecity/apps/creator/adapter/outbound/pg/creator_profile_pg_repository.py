from sqlalchemy import exists, func, insert, select, update
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
        user_id: int,
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
                user_id=user_id,
            )
            .returning(CreatorProfileOrm)
        )
        await self._session.commit()
        return CreatorProfileMapper.to_entity(result.scalar_one())

    async def find_by_id(self, profile_id: int) -> CreatorProfile | None:
        result = await self._session.execute(
            select(CreatorProfileOrm).where(CreatorProfileOrm.id == profile_id)
        )
        orm = result.scalar_one_or_none()
        return CreatorProfileMapper.to_entity(orm) if orm is not None else None

    async def find_by_user_id(self, user_id: int) -> CreatorProfile | None:
        result = await self._session.execute(
            select(CreatorProfileOrm).where(CreatorProfileOrm.user_id == user_id)
        )
        orm = result.scalar_one_or_none()
        return CreatorProfileMapper.to_entity(orm) if orm is not None else None

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
        q: str | None = None,
    ) -> list[CreatorProfile]:
        stmt = select(CreatorProfileOrm).where(CreatorProfileOrm.status == status.value)
        if category is not None:
            stmt = stmt.where(CreatorProfileOrm.primary_category == category)
        if q:
            pattern = f"%{q}%"
            stmt = stmt.where(
                CreatorProfileOrm.name.ilike(pattern)
                | CreatorProfileOrm.tagline.ilike(pattern)
            )
        stmt = (
            stmt.order_by(CreatorProfileOrm.created_at.desc(), CreatorProfileOrm.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [CreatorProfileMapper.to_entity(orm) for orm in result.scalars()]

    async def list_by_user_ids(
        self, user_ids: list[int], status: ProfileStatus
    ) -> list[CreatorProfile]:
        if not user_ids:
            return []
        result = await self._session.execute(
            select(CreatorProfileOrm)
            .where(CreatorProfileOrm.user_id.in_(user_ids))
            .where(CreatorProfileOrm.status == status.value)
        )
        return [CreatorProfileMapper.to_entity(orm) for orm in result.scalars()]

    async def list_categories(self, status: ProfileStatus) -> list[str]:
        result = await self._session.execute(
            select(CreatorProfileOrm.primary_category)
            .where(CreatorProfileOrm.status == status.value)
            .distinct()
            .order_by(CreatorProfileOrm.primary_category)
        )
        return list(result.scalars())

    async def update_status(
        self, profile_id: int, status: ProfileStatus
    ) -> CreatorProfile | None:
        result = await self._session.execute(
            update(CreatorProfileOrm)
            .where(CreatorProfileOrm.id == profile_id)
            .values(status=status.value)
            .returning(CreatorProfileOrm)
        )
        orm = result.scalar_one_or_none()
        await self._session.commit()
        return CreatorProfileMapper.to_entity(orm) if orm is not None else None

    async def update_profile(
        self,
        user_id: int,
        name: str,
        tagline: str,
        bio: str,
        location: str | None,
        primary_category: str,
    ) -> CreatorProfile | None:
        result = await self._session.execute(
            update(CreatorProfileOrm)
            .where(CreatorProfileOrm.user_id == user_id)
            .values(
                name=name,
                tagline=tagline,
                bio=bio,
                location=location,
                primary_category=primary_category,
            )
            .returning(CreatorProfileOrm)
        )
        orm = result.scalar_one_or_none()
        await self._session.commit()
        return CreatorProfileMapper.to_entity(orm) if orm is not None else None

    async def count_by_status(
        self, status: ProfileStatus, category: str | None, q: str | None = None
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(CreatorProfileOrm)
            .where(CreatorProfileOrm.status == status.value)
        )
        if category is not None:
            stmt = stmt.where(CreatorProfileOrm.primary_category == category)
        if q:
            pattern = f"%{q}%"
            stmt = stmt.where(
                CreatorProfileOrm.name.ilike(pattern)
                | CreatorProfileOrm.tagline.ilike(pattern)
            )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())
