from __future__ import annotations

from abc import ABC, abstractmethod


class CreditBalancePort(ABC):
    """크레딧 잔액 조회 포트 — 구현은 order(원장 소유)가 제공하고 main.py가 조립한다.

    payment가 체크아웃 준비 시 크레딧 적용액을 확정하는 데 쓴다.
    잔액은 조회 시점 스냅샷일 뿐이며, 실제 차감·재검증은 주문 생성 트랜잭션(order)이 수행한다.
    """

    @abstractmethod
    async def get_balance_krw(self, user_id: int) -> int:
        """사용자 크레딧 잔액(원) = 적립성 기입 합 − 차감성 기입 합."""
        ...
