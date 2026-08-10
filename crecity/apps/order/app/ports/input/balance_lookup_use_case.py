from __future__ import annotations

from abc import ABC, abstractmethod

from order.app.dtos.balance_lookup_dto import BalanceQuery, BalanceResult


class BalanceLookupUseCase(ABC):
    """잔액 조회 유스케이스 — 원장 기입 합산(크리에이터 적립·브랜드 환불 크레딧)."""

    @abstractmethod
    async def get_balance(self, query: BalanceQuery) -> BalanceResult: ...
