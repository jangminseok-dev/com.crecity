from __future__ import annotations

from core.database import session_scope
from hub.app.ports.output.credit_balance_port import CreditBalancePort
from order.adapter.outbound.pg.ledger_pg_repository import LedgerPgRepository


class OrderCreditBalanceGateway(CreditBalancePort):
    """허브 CreditBalancePort 계약의 order 구현 — main.py가 조립한다."""

    async def get_balance_krw(self, user_id: int) -> int:
        async with session_scope() as session:
            return await LedgerPgRepository(session=session).balance_krw(user_id)
