from __future__ import annotations

from datetime import datetime, timezone

from campaign.app.dtos.campaign_application_dto import (
    ApplicationResult,
    ApplicationsQuery,
    ApplyCommand,
)
from campaign.app.exceptions import (
    AlreadyAppliedError,
    CampaignNotFoundError,
    CreatorProfileRequiredError,
    NotCreatorAccountError,
)
from campaign.app.ports.input.campaign_application_use_case import CampaignApplicationUseCase
from campaign.app.ports.output.application_repository import ApplicationRepository
from campaign.app.ports.output.campaign_repository import CampaignRepository
from campaign.domain.entities.campaign_entity import CampaignApplication, NotCampaignOwnerError
from hub.app.ports.output.creator_ref_port import CreatorRefPort


class CampaignApplicationInteractor(CampaignApplicationUseCase):

    def __init__(
        self,
        campaigns: CampaignRepository,
        applications: ApplicationRepository,
        creators: CreatorRefPort,
    ) -> None:
        self._campaigns = campaigns
        self._applications = applications
        self._creators = creators

    async def _to_result(self, application: CampaignApplication) -> ApplicationResult:
        creator = await self._creators.get_creator_by_user_id(application.creator_user_id)
        return ApplicationResult(
            id=application.id,
            campaign_id=application.campaign_id,
            creator_user_id=application.creator_user_id,
            creator_name=creator.name if creator else "(프로필 없음)",
            creator_slug=creator.slug if creator else "",
            message=application.message,
            proposed_price_krw=application.proposed_price_krw,
            order_id=application.order_id,
            created_at=application.created_at,
        )

    async def apply(self, command: ApplyCommand) -> ApplicationResult:
        if command.account_type != "CREATOR":
            raise NotCreatorAccountError("크리에이터 계정만 지원할 수 있습니다.")
        if command.proposed_price_krw <= 0:
            raise ValueError("제안 견적은 0보다 커야 합니다.")
        campaign = await self._campaigns.find_by_id(command.campaign_id)
        if campaign is None:
            raise CampaignNotFoundError(f"공고를 찾을 수 없습니다: {command.campaign_id}")
        # 마감 공고·마감일 경과 409(도메인) — 스윕 주기와 무관하게 마감일이 정본
        campaign.ensure_open_for_application(datetime.now(timezone.utc))
        if await self._creators.get_creator_by_user_id(command.creator_user_id) is None:
            raise CreatorProfileRequiredError("프로필을 먼저 등록해야 지원할 수 있습니다.")
        if await self._applications.exists(command.campaign_id, command.creator_user_id):
            raise AlreadyAppliedError("이미 지원한 공고입니다.")

        application = await self._applications.create(
            campaign_id=command.campaign_id,
            creator_user_id=command.creator_user_id,
            message=command.message,
            proposed_price_krw=command.proposed_price_krw,
        )
        return await self._to_result(application)

    async def list_applications(self, query: ApplicationsQuery) -> list[ApplicationResult]:
        campaign = await self._campaigns.find_by_id(query.campaign_id)
        if campaign is None:
            raise CampaignNotFoundError(f"공고를 찾을 수 없습니다: {query.campaign_id}")
        if campaign.brand_user_id != query.requester_user_id:
            raise NotCampaignOwnerError("공고를 올린 브랜드만 지원자를 볼 수 있습니다.")
        applications = await self._applications.list_by_campaign(
            query.campaign_id, sort=query.sort, only_open=query.only_open
        )
        return [await self._to_result(application) for application in applications]
