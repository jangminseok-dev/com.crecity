from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from order.adapter.outbound.orm.ledger_entry_orm import LedgerEntryOrm
from order.app.ports.output.ledger_repository import LedgerRepository
from order.domain.entities.ledger_entry_entity import BALANCE_CREDIT_TYPES, BALANCE_DEBIT_TYPES

# 잔액 = 적립 합 − 차감 합 (append-only 원장에서 부호는 유형이 결정한다)
_SIGNED_AMOUNT = case(
    (LedgerEntryOrm.entry_type.in_(t.value for t in BALANCE_CREDIT_TYPES), LedgerEntryOrm.amount_krw),
    (LedgerEntryOrm.entry_type.in_(t.value for t in BALANCE_DEBIT_TYPES), -LedgerEntryOrm.amount_krw),
    else_=0,
)


class LedgerPgRepository(LedgerRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def balance_krw(self, user_id: int) -> int:
        result = await self._session.execute(
            select(func.coalesce(func.sum(_SIGNED_AMOUNT), 0)).where(
                LedgerEntryOrm.user_id == user_id
            )
        )
        return int(result.scalar_one())

    async def monthly_summary(
        self, user_id: int, year: int
    ) -> list[tuple[int, str, int, int]]:
        month = func.extract("month", LedgerEntryOrm.created_at)
        result = await self._session.execute(
            select(
                month,
                LedgerEntryOrm.entry_type,
                func.sum(LedgerEntryOrm.amount_krw),
                func.count(),
            )
            .where(
                LedgerEntryOrm.user_id == user_id,
                func.extract("year", LedgerEntryOrm.created_at) == year,
            )
            .group_by(month, LedgerEntryOrm.entry_type)
            .order_by(month, LedgerEntryOrm.entry_type)
        )
        return [
            (int(m), entry_type, int(total), int(count))
            for m, entry_type, total, count in result
        ]
