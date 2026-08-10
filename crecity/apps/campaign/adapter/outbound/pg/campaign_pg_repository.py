from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from campaign.adapter.outbound.mappers.campaign_mapper import CampaignMapper
from campaign.adapter.outbound.orm.campaign_orm import CampaignOrm
from campaign.app.ports.output.campaign_repository import CampaignRepository
from campaign.domain.entities.campaign_entity import Campaign, CampaignPlatform, CampaignStatus


class CampaignPgRepository(CampaignRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        brand_user_id: int,
        title: str,
        description: str,
        platform: CampaignPlatform,
        budget_krw: int,
    ) -> Campaign:
        result = await self._session.execute(
            insert(CampaignOrm)
            .values(
                brand_user_id=brand_user_id,
                title=title,
                description=description,
                platform=platform.value,
                budget_krw=budget_krw,
                status=CampaignStatus.OPEN.value,
            )
            .returning(CampaignOrm)
        )
        await self._session.commit()
        return CampaignMapper.to_entity(result.scalar_one())

    async def find_by_id(self, campaign_id: int) -> Campaign | None:
        result = await self._session.execute(
            select(CampaignOrm).where(CampaignOrm.id == campaign_id)
        )
        orm = result.scalar_one_or_none()
        return CampaignMapper.to_entity(orm) if orm is not None else None

    async def update_status(self, campaign_id: int, status: CampaignStatus) -> None:
        await self._session.execute(
            update(CampaignOrm).where(CampaignOrm.id == campaign_id).values(status=status.value)
        )
        await self._session.commit()

    async def list_by_status(
        self, status: CampaignStatus, limit: int, offset: int
    ) -> list[Campaign]:
        result = await self._session.execute(
            select(CampaignOrm)
            .where(CampaignOrm.status == status.value)
            .order_by(CampaignOrm.created_at.desc(), CampaignOrm.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return [CampaignMapper.to_entity(orm) for orm in result.scalars()]

    async def list_by_brand(self, brand_user_id: int) -> list[Campaign]:
        result = await self._session.execute(
            select(CampaignOrm)
            .where(CampaignOrm.brand_user_id == brand_user_id)
            .order_by(CampaignOrm.created_at.desc(), CampaignOrm.id.desc())
        )
        return [CampaignMapper.to_entity(orm) for orm in result.scalars()]
