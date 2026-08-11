from __future__ import annotations

from campaign.adapter.outbound.pg.application_pg_repository import ApplicationPgRepository
from campaign.adapter.outbound.pg.campaign_pg_repository import CampaignPgRepository
from core.database import session_scope
from hub.app.dtos.campaign_application_dto import CampaignApplicationSummary
from hub.app.ports.output.campaign_application_port import CampaignApplicationPort


class CampaignApplicationGateway(CampaignApplicationPort):
    """허브 CampaignApplicationPort 계약의 campaign 구현 — main.py가 조립한다."""

    async def get_payable_application(
        self, application_id: int
    ) -> CampaignApplicationSummary | None:
        async with session_scope() as session:
            application = await ApplicationPgRepository(session).find_by_id(application_id)
            if application is None or not application.is_payable():
                return None
            campaign = await CampaignPgRepository(session).find_by_id(application.campaign_id)
        if campaign is None:  # FK가 보장 — 데이터 손상 신호
            return None
        return CampaignApplicationSummary(
            application_id=application.id,
            campaign_id=campaign.id,
            title=campaign.title,
            price_krw=application.proposed_price_krw,
            brand_user_id=campaign.brand_user_id,
            creator_user_id=application.creator_user_id,
        )

    async def mark_paid(self, application_id: int, order_id: int) -> None:
        async with session_scope() as session:
            await ApplicationPgRepository(session).mark_paid(application_id, order_id)
