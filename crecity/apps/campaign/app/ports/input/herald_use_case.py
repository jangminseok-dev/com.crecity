from __future__ import annotations

from abc import ABC, abstractmethod

from campaign.app.dtos.herald_dto import HeraldQuery, HeraldResponse


class HeraldUseCase(ABC):
    """캠페인 (campaign) 유스케이스 — 역경매 공고·지원 담당."""

    @abstractmethod
    async def introduce_myself(self, query: HeraldQuery) -> HeraldResponse:
        """캠페인 (campaign)의 자기소개 메소드."""
        ...
