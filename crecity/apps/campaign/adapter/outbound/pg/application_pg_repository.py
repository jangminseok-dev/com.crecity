from sqlalchemy import exists, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from campaign.adapter.outbound.mappers.campaign_mapper import CampaignMapper
from campaign.adapter.outbound.orm.campaign_orm import CampaignApplicationOrm
from campaign.app.ports.output.application_repository import ApplicationRepository
from campaign.domain.entities.campaign_entity import CampaignApplication
from campaign.domain.value_objects.application_sort import ApplicationSort
from hub.adapter.outbound.pg.outbox_pg_store import enqueue_events
from hub.app.dtos.outbox_event_dto import OutboxEvent


def _order_by(sort: ApplicationSort) -> list:
    """정렬 절 — 동점이면 id로 갈라 순서가 흔들리지 않게 한다."""
    if sort is ApplicationSort.LATEST:
        return [CampaignApplicationOrm.created_at.desc(), CampaignApplicationOrm.id.desc()]
    if sort is ApplicationSort.PRICE_ASC:
        return [CampaignApplicationOrm.proposed_price_krw.asc(), CampaignApplicationOrm.id.asc()]
    if sort is ApplicationSort.PRICE_DESC:
        return [CampaignApplicationOrm.proposed_price_krw.desc(), CampaignApplicationOrm.id.asc()]
    return [CampaignApplicationOrm.created_at.asc(), CampaignApplicationOrm.id.asc()]


class ApplicationPgRepository(ApplicationRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        campaign_id: int,
        creator_user_id: int,
        message: str,
        proposed_price_krw: int,
        events: list[OutboxEvent] | None = None,
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
        enqueue_events(self._session, events or [])  # 지원+알림 = 단일 커밋
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

    async def list_by_campaign(
        self,
        campaign_id: int,
        sort: ApplicationSort = ApplicationSort.OLDEST,
        only_open: bool = False,
    ) -> list[CampaignApplication]:
        statement = select(CampaignApplicationOrm).where(
            CampaignApplicationOrm.campaign_id == campaign_id
        )
        if only_open:
            # 이미 수락(결제)된 지원은 더 볼 일이 없다
            statement = statement.where(CampaignApplicationOrm.order_id.is_(None))
        result = await self._session.execute(statement.order_by(*_order_by(sort)))
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
