from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from creator.adapter.outbound.mappers.creator_package_mapper import CreatorPackageMapper
from creator.adapter.outbound.orm.creator_package_orm import CreatorPackageOrm
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
    ) -> CreatorPackage:
        result = await self._session.execute(
            insert(CreatorPackageOrm)
            .values(
                profile_id=profile_id,
                platform=platform.value,
                title=title,
                description=description,
                price_krw=price_krw,
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
    ) -> CreatorPackage | None:
        result = await self._session.execute(
            update(CreatorPackageOrm)
            .where(CreatorPackageOrm.id == package_id)
            .values(
                platform=platform.value,
                title=title,
                description=description,
                price_krw=price_krw,
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
