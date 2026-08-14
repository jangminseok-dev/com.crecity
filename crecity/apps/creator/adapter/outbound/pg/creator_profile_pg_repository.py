from sqlalchemy import exists, func, insert, nulls_last, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from creator.adapter.outbound.mappers.creator_profile_mapper import CreatorProfileMapper
from creator.adapter.outbound.orm.creator_package_orm import CreatorPackageOrm
from creator.adapter.outbound.orm.creator_profile_orm import CreatorProfileOrm
from creator.app.ports.output.creator_profile_repository import CreatorProfileRepository
from creator.domain.entities.creator_profile_entity import CreatorProfile, ProfileStatus
from creator.domain.value_objects.profile_sort import ProfileSort


def _listing_conditions(
    category: str | None,
    q: str | None,
    platform: str | None,
    price_min: int | None,
    price_max: int | None,
    location: str | None,
) -> list:
    """목록·카운트가 공유하는 검색 필터(§3.1) — 목록과 총계가 항상 같은 조건을 본다."""
    conditions = []
    if category is not None:
        conditions.append(CreatorProfileOrm.primary_category == category)
    if q:
        pattern = f"%{q}%"
        conditions.append(
            CreatorProfileOrm.name.ilike(pattern) | CreatorProfileOrm.tagline.ilike(pattern)
        )
    if location:
        conditions.append(CreatorProfileOrm.location.ilike(f"%{location}%"))
    if platform or price_min is not None or price_max is not None:
        # 조건(플랫폼·가격대)을 동시에 만족하는 패키지가 하나라도 있는 프로필
        packages = select(CreatorPackageOrm.id).where(
            CreatorPackageOrm.profile_id == CreatorProfileOrm.id
        )
        if platform:
            packages = packages.where(CreatorPackageOrm.platform == platform)
        if price_min is not None:
            packages = packages.where(CreatorPackageOrm.price_krw >= price_min)
        if price_max is not None:
            packages = packages.where(CreatorPackageOrm.price_krw <= price_max)
        conditions.append(packages.exists())
    return conditions


def _listing_order_by(sort: ProfileSort) -> list:
    """정렬 절(§3.1, 갭 #45) — 가격은 최저 패키지 가격, 패키지 없는 프로필(NULL)은 항상 뒤로."""
    if sort in (ProfileSort.PRICE_ASC, ProfileSort.PRICE_DESC):
        min_price = (
            select(func.min(CreatorPackageOrm.price_krw))
            .where(CreatorPackageOrm.profile_id == CreatorProfileOrm.id)
            .scalar_subquery()
        )
        direction = min_price.asc() if sort is ProfileSort.PRICE_ASC else min_price.desc()
        return [nulls_last(direction), CreatorProfileOrm.id.desc()]
    return [CreatorProfileOrm.created_at.desc(), CreatorProfileOrm.id.desc()]


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
        platform: str | None = None,
        price_min: int | None = None,
        price_max: int | None = None,
        location: str | None = None,
        sort: ProfileSort = ProfileSort.LATEST,
    ) -> list[CreatorProfile]:
        stmt = select(CreatorProfileOrm).where(
            CreatorProfileOrm.status == status.value,
            *_listing_conditions(category, q, platform, price_min, price_max, location),
        )
        stmt = stmt.order_by(*_listing_order_by(sort)).limit(limit).offset(offset)
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
        self,
        status: ProfileStatus,
        category: str | None,
        q: str | None = None,
        platform: str | None = None,
        price_min: int | None = None,
        price_max: int | None = None,
        location: str | None = None,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(CreatorProfileOrm)
            .where(
                CreatorProfileOrm.status == status.value,
                *_listing_conditions(category, q, platform, price_min, price_max, location),
            )
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())
