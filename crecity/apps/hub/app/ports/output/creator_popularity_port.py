from __future__ import annotations

from abc import ABC, abstractmethod

from hub.app.dtos.creator_popularity_dto import CreatorOrderCount


class CreatorPopularityPort(ABC):
    """크리에이터 인기 순위 포트 — 구현은 order가 제공하고 main.py가 조립한다."""

    @abstractmethod
    async def top_creators_by_recent_orders(self, days: int, limit: int) -> list[CreatorOrderCount]:
        """최근 days일 주문 수 상위 크리에이터(환불·취소 제외) — 주문 수 내림차순."""
        ...
