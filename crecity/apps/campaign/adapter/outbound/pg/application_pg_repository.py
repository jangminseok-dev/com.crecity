from sqlalchemy import exists, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from campaign.adapter.outbound.mappers.campaign_mapper import CampaignMapper
from campaign.adapter.outbound.orm.campaign_orm import CampaignApplicationOrm
from campaign.app.ports.output.application_repository import ApplicationRepository
from campaign.domain.entities.campaign_entity import CampaignApplication


class ApplicationPgRepository(ApplicationRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, campaign_id: int, creator_user_id: int, message: str, proposed_price_krw: int
    ) -> CampaignApplication:
        result = await self._session.execute(
            insert(CampaignApplicationOrm)
            .values(
                campaign_id=campaign_id,
                creator_user_id=creator_user_id,
                message=message,
                proposed_price_krw=proposed_price_krw,
            )
            .returning(CampaignApplicationOrm)
        )
        await self._session.commit()
        return CampaignMapper.application_to_entity(result.scalar_one())

    async def exists(self, campaign_id: int, creator_user_id: int) -> bool:
        result = await self._session.execute(
            select(
                exists().where(
                    CampaignApplicationOrm.campaign_id == campaign_id,
                    CampaignApplicationOrm.creator_user_id == creator_user_id,
                )
            )
        )
        return bool(result.scalar())

    async def list_by_campaign(self, campaign_id: int) -> list[CampaignApplication]:
        result = await self._session.execute(
            select(CampaignApplicationOrm)
            .where(CampaignApplicationOrm.campaign_id == campaign_id)
            .order_by(CampaignApplicationOrm.created_at, CampaignApplicationOrm.id)
        )
        return [CampaignMapper.application_to_entity(orm) for orm in result.scalars()]

    async def find_by_id(self, application_id: int) -> CampaignApplication | None:
        orm = await self._session.get(CampaignApplicationOrm, application_id)
        return CampaignMapper.application_to_entity(orm) if orm is not None else None

    async def mark_paid(self, application_id: int, order_id: int) -> None:
        await self._session.execute(
            update(CampaignApplicationOrm)
            .where(CampaignApplicationOrm.id == application_id)
            .values(order_id=order_id)
        )
        await self._session.commit()
