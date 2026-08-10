from __future__ import annotations

from abc import ABC, abstractmethod

from campaign.app.dtos.campaign_listing_dto import CampaignDetailQuery, OpenCampaignsQuery
from campaign.app.dtos.campaign_posting_dto import CampaignResult


class CampaignListingUseCase(ABC):
    """공고 조회 유스케이스 — OPEN 목록(크리에이터용)·상세·브랜드 내 공고."""

    @abstractmethod
    async def list_open(self, query: OpenCampaignsQuery) -> list[CampaignResult]:
        """지원 가능한 공고 — 최신순."""
        ...

    @abstractmethod
    async def get_campaign(self, query: CampaignDetailQuery) -> CampaignResult:
        """공고 상세.

        Raises:
            CampaignNotFoundError
        """
        ...

    @abstractmethod
    async def list_my_campaigns(self, brand_user_id: int) -> list[CampaignResult]:
        """브랜드가 올린 공고 — 최신순."""
        ...
