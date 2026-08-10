from __future__ import annotations

from campaign.app.dtos.campaign_posting_dto import (
    CampaignResult,
    CloseCampaignCommand,
    PostCampaignCommand,
)
from campaign.app.exceptions import CampaignNotFoundError, NotBrandAccountError
from campaign.app.ports.input.campaign_posting_use_case import CampaignPostingUseCase
from campaign.app.ports.output.campaign_repository import CampaignRepository
from campaign.domain.entities.campaign_entity import Campaign, CampaignPlatform


def _parse_platform(raw: str) -> CampaignPlatform:
    try:
        return CampaignPlatform(raw)
    except ValueError:
        allowed = ", ".join(p.value for p in CampaignPlatform)
        raise ValueError(f"지원하지 않는 플랫폼입니다: {raw} (허용: {allowed})")


def to_result(campaign: Campaign) -> CampaignResult:
    return CampaignResult(
        id=campaign.id,
        brand_user_id=campaign.brand_user_id,
        title=campaign.title,
        description=campaign.description,
        platform=campaign.platform.value,
        budget_krw=campaign.budget_krw,
        status=campaign.status.value,
        created_at=campaign.created_at,
    )


class CampaignPostingInteractor(CampaignPostingUseCase):

    def __init__(self, campaigns: CampaignRepository) -> None:
        self._campaigns = campaigns

    async def post(self, command: PostCampaignCommand) -> CampaignResult:
        if command.account_type != "BRAND":
            raise NotBrandAccountError("브랜드 계정만 공고를 올릴 수 있습니다.")
        if command.budget_krw <= 0:
            raise ValueError("예산은 0보다 커야 합니다.")
        campaign = await self._campaigns.create(
            brand_user_id=command.brand_user_id,
            title=command.title,
            description=command.description,
            platform=_parse_platform(command.platform),
            budget_krw=command.budget_krw,
        )
        return to_result(campaign)

    async def close(self, command: CloseCampaignCommand) -> CampaignResult:
        campaign = await self._campaigns.find_by_id(command.campaign_id)
        if campaign is None:
            raise CampaignNotFoundError(f"공고를 찾을 수 없습니다: {command.campaign_id}")
        closed = campaign.close(command.actor_user_id)  # 소유·상태 검증은 도메인
        await self._campaigns.update_status(closed.id, closed.status)
        return to_result(closed)
