from __future__ import annotations

from order.app.dtos.balance_lookup_dto import BalanceQuery, BalanceResult
from order.app.ports.input.balance_lookup_use_case import BalanceLookupUseCase
from order.app.ports.output.ledger_repository import LedgerRepository


class BalanceLookupInteractor(BalanceLookupUseCase):

    def __init__(self, ledger: LedgerRepository) -> None:
        self._ledger = ledger

    async def get_balance(self, query: BalanceQuery) -> BalanceResult:
        balance = await self._ledger.balance_krw(query.user_id)
        return BalanceResult(user_id=query.user_id, balance_krw=balance)
