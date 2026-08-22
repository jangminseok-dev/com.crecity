from __future__ import annotations

from abc import ABC, abstractmethod

from campaign.app.dtos.campaign_application_dto import (
    ApplicationResult,
    ApplicationsQuery,
    ApplyCommand,
    MyApplicationResult,
    MyApplicationsQuery,
)


class CampaignApplicationUseCase(ABC):
    """공고 지원 유스케이스 — 크리에이터가 자체 견적으로 제안한다."""

    @abstractmethod
    async def apply(self, command: ApplyCommand) -> ApplicationResult:
        """공고에 지원한다(공고당 1회, OPEN만).

        Raises:
            CampaignNotFoundError · NotCreatorAccountError · CreatorProfileRequiredError ·
            AlreadyAppliedError · InvalidCampaignStateError(도메인, 409) · ValueError(견적 검증)
        """
        ...

    @abstractmethod
    async def list_applications(self, query: ApplicationsQuery) -> list[ApplicationResult]:
        """공고의 지원자 목록 — 공고를 올린 브랜드만.

        Raises:
            CampaignNotFoundError · NotCampaignOwnerError(도메인, 403)
        """
        ...

    @abstractmethod
    async def list_my_applications(
        self, query: MyApplicationsQuery
    ) -> list[MyApplicationResult]:
        """크리에이터 본인의 지원 내역 — 최신순(갭 #103).

        Raises:
            NotCreatorAccountError(403)
        """
        ...
