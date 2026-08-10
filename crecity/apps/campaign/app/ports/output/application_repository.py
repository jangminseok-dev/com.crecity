from __future__ import annotations

from abc import ABC, abstractmethod

from campaign.domain.entities.campaign_entity import CampaignApplication


class ApplicationRepository(ABC):
    """지원서 영속성 포트."""

    @abstractmethod
    async def create(
        self, campaign_id: int, creator_user_id: int, message: str, proposed_price_krw: int
    ) -> CampaignApplication: ...

    @abstractmethod
    async def exists(self, campaign_id: int, creator_user_id: int) -> bool: ...

    @abstractmethod
    async def list_by_campaign(self, campaign_id: int) -> list[CampaignApplication]:
        """공고의 지원서 — 오래된 순(먼저 지원한 순)."""
        ...
