from __future__ import annotations

from abc import ABC, abstractmethod

from campaign.domain.entities.campaign_entity import Campaign, CampaignPlatform, CampaignStatus


class CampaignRepository(ABC):
    """공고 영속성 포트 (도메인어 명명 예외)."""

    @abstractmethod
    async def create(
        self,
        brand_user_id: int,
        title: str,
        description: str,
        platform: CampaignPlatform,
        budget_krw: int,
    ) -> Campaign: ...

    @abstractmethod
    async def find_by_id(self, campaign_id: int) -> Campaign | None: ...

    @abstractmethod
    async def update_status(self, campaign_id: int, status: CampaignStatus) -> None: ...

    @abstractmethod
    async def list_by_status(
        self, status: CampaignStatus, limit: int, offset: int
    ) -> list[Campaign]:
        """상태 필터 목록 — 최신순."""
        ...

    @abstractmethod
    async def list_by_brand(self, brand_user_id: int) -> list[Campaign]:
        """브랜드가 올린 공고 — 최신순."""
        ...
