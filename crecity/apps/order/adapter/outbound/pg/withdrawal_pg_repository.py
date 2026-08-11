from __future__ import annotations

from sqlalchemy import func, insert, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from order.adapter.outbound.orm.ledger_entry_orm import LedgerEntryOrm
from order.adapter.outbound.orm.withdrawal_orm import WithdrawalOrm
from order.adapter.outbound.pg.ledger_pg_repository import _SIGNED_AMOUNT
from order.app.ports.output.withdrawal_repository import WithdrawalRepository
from order.domain.entities.ledger_entry_entity import LedgerEntryDraft, LedgerEntryType
from order.domain.entities.withdrawal_entity import Withdrawal, WithdrawalStatus


def _to_entity(orm: WithdrawalOrm) -> Withdrawal:
    return Withdrawal(
        id=orm.id,
        user_id=orm.user_id,
        amount_krw=orm.amount_krw,
        tax_krw=orm.tax_krw,
        payout_krw=orm.payout_krw,
        bank_name=orm.bank_name,
        account_number=orm.account_number,
        account_holder=orm.account_holder,
        status=WithdrawalStatus(orm.status),
        created_at=orm.created_at,
        settled_at=orm.settled_at,
    )


class WithdrawalPgRepository(WithdrawalRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_if_balance_sufficient(
        self,
        user_id: int,
        amount_krw: int,
        tax_krw: int,
        payout_krw: int,
        bank_name: str,
        account_number: str,
        account_holder: str,
    ) -> Withdrawal | None:
        # 사용자 단위 트랜잭션 잠금 — 동시 인출 요청의 과인출을 차단한다
        await self._session.execute(
            text("SELECT pg_advisory_xact_lock(:key)").bindparams(key=user_id)
        )
        balance = await self._session.execute(
            select(func.coalesce(func.sum(_SIGNED_AMOUNT), 0)).where(
                LedgerEntryOrm.user_id == user_id
            )
        )
        if int(balance.scalar_one()) < amount_krw:
            await self._session.rollback()
            return None

        result = await self._session.execute(
            insert(WithdrawalOrm)
            .values(
                user_id=user_id,
                amount_krw=amount_krw,
                tax_krw=tax_krw,
                payout_krw=payout_krw,
                bank_name=bank_name,
                account_number=account_number,
                account_holder=account_holder,
                status=WithdrawalStatus.REQUESTED.value,
            )
            .returning(WithdrawalOrm)
        )
        orm = result.scalar_one()
        await self._session.execute(
            insert(LedgerEntryOrm).values(
                withdrawal_id=orm.id,
                order_id=None,
                entry_type=LedgerEntryType.WITHDRAWAL.value,
                user_id=user_id,
                amount_krw=amount_krw,
            )
        )
        await self._session.commit()
        return _to_entity(orm)

    async def find_by_id(self, withdrawal_id: int) -> Withdrawal | None:
        orm = await self._session.get(WithdrawalOrm, withdrawal_id)
        return _to_entity(orm) if orm is not None else None

    async def list_by_user(self, user_id: int) -> list[Withdrawal]:
        result = await self._session.execute(
            select(WithdrawalOrm)
            .where(WithdrawalOrm.user_id == user_id)
            .order_by(WithdrawalOrm.created_at.desc(), WithdrawalOrm.id.desc())
        )
        return [_to_entity(orm) for orm in result.scalars()]

    async def list_by_status(self, status: WithdrawalStatus) -> list[Withdrawal]:
        result = await self._session.execute(
            select(WithdrawalOrm)
            .where(WithdrawalOrm.status == status.value)
            .order_by(WithdrawalOrm.created_at, WithdrawalOrm.id)
        )
        return [_to_entity(orm) for orm in result.scalars()]

    async def save_settlement(
        self, withdrawal: Withdrawal, entries: list[LedgerEntryDraft]
    ) -> Withdrawal:
        result = await self._session.execute(
            update(WithdrawalOrm)
            .where(WithdrawalOrm.id == withdrawal.id)
            .values(status=withdrawal.status.value, settled_at=func.now())
            .returning(WithdrawalOrm)
        )
        orm = result.scalar_one()
        for entry in entries:
            await self._session.execute(
                insert(LedgerEntryOrm).values(
                    withdrawal_id=withdrawal.id,
                    order_id=None,
                    entry_type=entry.entry_type.value,
                    user_id=entry.user_id,
                    amount_krw=entry.amount_krw,
                )
            )
        await self._session.commit()
        return _to_entity(orm)
