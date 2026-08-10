from __future__ import annotations

from abc import ABC, abstractmethod

from campaign.app.dtos.campaign_posting_dto import (
    CampaignResult,
    CloseCampaignCommand,
    PostCampaignCommand,
)


class CampaignPostingUseCase(ABC):
    """공고 등록·마감 유스케이스 — 브랜드 전용(역경매의 수요 측)."""

    @abstractmethod
    async def post(self, command: PostCampaignCommand) -> CampaignResult:
        """공고를 OPEN 상태로 등록한다.

        Raises:
            NotBrandAccountError · ValueError(플랫폼·예산 검증)
        """
        ...

    @abstractmethod
    async def close(self, command: CloseCampaignCommand) -> CampaignResult:
        """공고를 마감한다 — 이후 지원 불가.

        Raises:
            CampaignNotFoundError · NotCampaignOwnerError(도메인, 403) ·
            InvalidCampaignStateError(도메인, 409)
        """
        ...
