from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from creator.adapter.outbound.mappers.creator_package_mapper import CreatorPackageMapper
from creator.adapter.outbound.orm.creator_package_orm import CreatorPackageOrm
from creator.adapter.outbound.orm.creator_profile_orm import CreatorProfileOrm
from creator.app.ports.output.creator_package_repository import CreatorPackageRepository
from creator.domain.entities.creator_package_entity import CreatorPackage, PackagePlatform


class CreatorPackagePgRepository(CreatorPackageRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        profile_id: int,
        platform: PackagePlatform,
        title: str,
        description: str,
        price_krw: int,
        revision_limit: int,
        usage_rights: str,
    ) -> CreatorPackage:
        result = await self._session.execute(
            insert(CreatorPackageOrm)
            .values(
                profile_id=profile_id,
                platform=platform.value,
                title=title,
                description=description,
                price_krw=price_krw,
                revision_limit=revision_limit,
                usage_rights=usage_rights,
            )
            .returning(CreatorPackageOrm)
        )
        await self._session.commit()
        return CreatorPackageMapper.to_entity(result.scalar_one())

    async def find_by_id(self, package_id: int) -> CreatorPackage | None:
        result = await self._session.execute(
            select(CreatorPackageOrm).where(CreatorPackageOrm.id == package_id)
        )
        orm = result.scalar_one_or_none()
        return CreatorPackageMapper.to_entity(orm) if orm is not None else None

    async def update(
        self,
        package_id: int,
        platform: PackagePlatform,
        title: str,
        description: str,
        price_krw: int,
        revision_limit: int,
        usage_rights: str,
    ) -> CreatorPackage | None:
        result = await self._session.execute(
            update(CreatorPackageOrm)
            .where(CreatorPackageOrm.id == package_id)
            .values(
                platform=platform.value,
                title=title,
                description=description,
                price_krw=price_krw,
                revision_limit=revision_limit,
                usage_rights=usage_rights,
            )
            .returning(CreatorPackageOrm)
        )
        orm = result.scalar_one_or_none()
        await self._session.commit()
        return CreatorPackageMapper.to_entity(orm) if orm is not None else None

    async def delete(self, package_id: int) -> bool:
        result = await self._session.execute(
            delete(CreatorPackageOrm).where(CreatorPackageOrm.id == package_id)
        )
        await self._session.commit()
        return result.rowcount > 0

    async def list_by_profile_id(self, profile_id: int) -> list[CreatorPackage]:
        result = await self._session.execute(
            select(CreatorPackageOrm)
            .where(CreatorPackageOrm.profile_id == profile_id)
            .order_by(CreatorPackageOrm.price_krw)
        )
        return [CreatorPackageMapper.to_entity(orm) for orm in result.scalars().all()]

    async def min_prices_by_profile_ids(self, profile_ids: list[int]) -> dict[int, int]:
        if not profile_ids:
            return {}
        result = await self._session.execute(
            select(CreatorPackageOrm.profile_id, func.min(CreatorPackageOrm.price_krw))
            .where(CreatorPackageOrm.profile_id.in_(profile_ids))
            .group_by(CreatorPackageOrm.profile_id)
        )
        return {profile_id: int(price) for profile_id, price in result}

    async def platforms_by_profile_ids(self, profile_ids: list[int]) -> dict[int, set[str]]:
        if not profile_ids:
            return {}
        result = await self._session.execute(
            select(CreatorPackageOrm.profile_id, CreatorPackageOrm.platform)
            .where(CreatorPackageOrm.profile_id.in_(profile_ids))
            .distinct()
        )
        platforms: dict[int, set[str]] = {}
        for profile_id, platform in result:
            platforms.setdefault(profile_id, set()).add(platform)
        return platforms

    async def classify_by_package_ids(
        self, package_ids: list[int]
    ) -> dict[int, tuple[str, str]]:
        if not package_ids:
            return {}
        # 프로필 조인은 같은 스포크 안이라 허용 — 카테고리는 프로필, 플랫폼은 패키지 소유
        result = await self._session.execute(
            select(
                CreatorPackageOrm.id,
                CreatorProfileOrm.primary_category,
                CreatorPackageOrm.platform,
            )
            .join(CreatorProfileOrm, CreatorProfileOrm.id == CreatorPackageOrm.profile_id)
            .where(CreatorPackageOrm.id.in_(package_ids))
        )
        return {
            package_id: (category, platform) for package_id, category, platform in result
        }
