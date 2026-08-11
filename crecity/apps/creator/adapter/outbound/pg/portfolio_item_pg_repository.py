from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from creator.adapter.outbound.mappers.portfolio_item_mapper import to_entity
from creator.adapter.outbound.orm.portfolio_item_orm import PortfolioItemOrm
from creator.app.ports.output.portfolio_item_repository import PortfolioItemRepository
from creator.domain.entities.portfolio_item_entity import PortfolioItem


class PortfolioItemPgRepository(PortfolioItemRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, profile_id: int, file_name: str) -> PortfolioItem:
        orm = PortfolioItemOrm(profile_id=profile_id, file_name=file_name)
        self._session.add(orm)
        await self._session.commit()
        await self._session.refresh(orm)
        return to_entity(orm)

    async def find_by_id(self, item_id: int) -> PortfolioItem | None:
        orm = await self._session.get(PortfolioItemOrm, item_id)
        return to_entity(orm) if orm is not None else None

    async def list_by_profile_id(self, profile_id: int) -> list[PortfolioItem]:
        stmt = (
            select(PortfolioItemOrm)
            .where(PortfolioItemOrm.profile_id == profile_id)
            .order_by(PortfolioItemOrm.id)
        )
        return [to_entity(orm) for orm in (await self._session.scalars(stmt)).all()]

    async def count_by_profile_id(self, profile_id: int) -> int:
        stmt = select(func.count()).select_from(PortfolioItemOrm).where(
            PortfolioItemOrm.profile_id == profile_id
        )
        return (await self._session.execute(stmt)).scalar_one()

    async def first_file_names_by_profile_ids(self, profile_ids: list[int]) -> dict[int, str]:
        if not profile_ids:
            return {}
        stmt = (
            select(PortfolioItemOrm.profile_id, PortfolioItemOrm.file_name)
            .distinct(PortfolioItemOrm.profile_id)  # PG DISTINCT ON — 프로필별 등록순 첫 장
            .where(PortfolioItemOrm.profile_id.in_(profile_ids))
            .order_by(PortfolioItemOrm.profile_id, PortfolioItemOrm.id)
        )
        result = await self._session.execute(stmt)
        return dict(result.all())

    async def delete(self, item_id: int) -> bool:
        result = await self._session.execute(
            delete(PortfolioItemOrm).where(PortfolioItemOrm.id == item_id)
        )
        await self._session.commit()
        return result.rowcount > 0
