from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from order.adapter.outbound.orm.ledger_entry_orm import LedgerEntryOrm
from order.app.ports.output.ledger_repository import LedgerRepository
from order.domain.entities.ledger_entry_entity import BALANCE_CREDIT_TYPES


class LedgerPgRepository(LedgerRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def balance_krw(self, user_id: int) -> int:
        result = await self._session.execute(
            select(func.coalesce(func.sum(LedgerEntryOrm.amount_krw), 0)).where(
                LedgerEntryOrm.user_id == user_id,
                LedgerEntryOrm.entry_type.in_(t.value for t in BALANCE_CREDIT_TYPES),
            )
        )
        return int(result.scalar_one())
