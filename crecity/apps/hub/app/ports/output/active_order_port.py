from __future__ import annotations

from abc import ABC, abstractmethod


class ActiveOrderPort(ABC):
    """진행 중 주문 존재 여부 포트 — 구현은 order가 제공하고 main.py가 조립한다.

    §3.8: 활성 주문이 남은 계정은 삭제할 수 없다(거래 상대 보호).
    """

    @abstractmethod
    async def has_active_orders(self, user_id: int) -> bool:
        """브랜드·크리에이터 어느 쪽으로든 종결되지 않은 주문이 있으면 True."""
        ...
