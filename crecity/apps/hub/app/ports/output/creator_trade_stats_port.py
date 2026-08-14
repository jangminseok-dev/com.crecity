from __future__ import annotations

from abc import ABC, abstractmethod

from hub.app.dtos.creator_trade_stats_dto import CreatorTradeStats


class CreatorTradeStatsPort(ABC):
    """크리에이터 거래 이력 조회 포트(갭 #66) — 구현은 order가 제공한다.

    주문은 order 소유이므로 creator는 이 계약으로만 자기 프로필의 거래 실적을 읽는다.
    """

    @abstractmethod
    async def get_creator_stats(self, creator_user_id: int) -> CreatorTradeStats: ...
