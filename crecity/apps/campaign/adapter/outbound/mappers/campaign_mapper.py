from campaign.adapter.outbound.orm.campaign_orm import CampaignApplicationOrm, CampaignOrm
from campaign.domain.entities.campaign_entity import (
    Campaign,
    CampaignApplication,
    CampaignPlatform,
    CampaignStatus,
)


class CampaignMapper:
    """Campaign/Application ORM(영속성) ↔ 도메인 변환을 담당한다."""

    @staticmethod
    def to_entity(orm: CampaignOrm) -> Campaign:
        return Campaign(
            id=orm.id,
            brand_user_id=orm.brand_user_id,
            title=orm.title,
            description=orm.description,
            platform=CampaignPlatform(orm.platform),
            budget_krw=orm.budget_krw,
            status=CampaignStatus(orm.status),
            created_at=orm.created_at,
        )

    @staticmethod
    def application_to_entity(orm: CampaignApplicationOrm) -> CampaignApplication:
        return CampaignApplication(
            id=orm.id,
            campaign_id=orm.campaign_id,
            creator_user_id=orm.creator_user_id,
            message=orm.message,
            proposed_price_krw=orm.proposed_price_krw,
            created_at=orm.created_at,
        )
