from __future__ import annotations

from core.database import session_scope
from hub.app.dtos.withdrawal_settlement_dto import AnnualPayoutSummary, WithdrawalSummary
from hub.app.ports.output.withdrawal_settlement_port import WithdrawalSettlementPort
from order.adapter.outbound.pg.withdrawal_pg_repository import WithdrawalPgRepository
from order.app.withdrawal_events import withdrawal_event
from order.domain.entities.ledger_entry_entity import LedgerEntryDraft, LedgerEntryType
from order.domain.entities.withdrawal_entity import (
    InvalidWithdrawalStateError,
    Withdrawal,
    WithdrawalStatus,
)
from order.domain.value_objects.annual_payout import AnnualPayout


def _to_summary(withdrawal: Withdrawal) -> WithdrawalSummary:
    return WithdrawalSummary(
        id=withdrawal.id,
        creator_user_id=withdrawal.user_id,
        amount_krw=withdrawal.amount_krw,
        tax_krw=withdrawal.tax_krw,
        payout_krw=withdrawal.payout_krw,
        bank_name=withdrawal.bank_name,
        account_number=withdrawal.account_number,
        account_holder=withdrawal.account_holder,
        status=withdrawal.status.value,
        created_at=withdrawal.created_at,
    )


class OrderWithdrawalSettlementGateway(WithdrawalSettlementPort):
    """허브 WithdrawalSettlementPort 계약의 order 구현 — main.py가 조립한다."""

    async def list_pending(self) -> list[WithdrawalSummary]:
        async with session_scope() as session:
            pending = await WithdrawalPgRepository(session).list_by_status(
                WithdrawalStatus.REQUESTED
            )
        return [_to_summary(w) for w in pending]

    async def annual_summary(self, year: int) -> list[AnnualPayoutSummary]:
        async with session_scope() as session:
            paid = await WithdrawalPgRepository(session).list_paid_in_year(year)

        by_user: dict[int, list[Withdrawal]] = {}
        for withdrawal in paid:
            by_user.setdefault(withdrawal.user_id, []).append(withdrawal)
        summaries = [
            AnnualPayoutSummary(
                creator_user_id=user_id,
                account_holder=items[-1].account_holder,  # 최근 지급의 예금주
                count=payout.count,
                total_amount_krw=payout.total_amount_krw,
                total_tax_krw=payout.total_tax_krw,
                total_payout_krw=payout.total_payout_krw,
            )
            for user_id, items in by_user.items()
            if (payout := AnnualPayout.of(user_id, items))
        ]
        return sorted(summaries, key=lambda s: s.total_amount_krw, reverse=True)

    async def complete(self, withdrawal_id: int) -> WithdrawalSummary | None:
        async with session_scope() as session:
            repository = WithdrawalPgRepository(session)
            withdrawal = await repository.find_by_id(withdrawal_id)
            if withdrawal is None:
                return None
            try:
                paid = withdrawal.mark_paid()
            except InvalidWithdrawalStateError as error:
                raise ValueError(str(error))
            saved = await repository.save_settlement(
                paid, entries=[], events=[withdrawal_event("withdrawal.paid", paid)]
            )
        return _to_summary(saved)

    async def fail(self, withdrawal_id: int) -> WithdrawalSummary | None:
        async with session_scope() as session:
            repository = WithdrawalPgRepository(session)
            withdrawal = await repository.find_by_id(withdrawal_id)
            if withdrawal is None:
                return None
            try:
                failed = withdrawal.mark_failed()
            except InvalidWithdrawalStateError as error:
                raise ValueError(str(error))
            saved = await repository.save_settlement(
                failed,
                entries=[
                    LedgerEntryDraft(
                        entry_type=LedgerEntryType.WITHDRAWAL_REVERSAL,
                        user_id=withdrawal.user_id,
                        amount_krw=withdrawal.amount_krw,
                    )
                ],
                events=[withdrawal_event("withdrawal.failed", failed)],
            )
        return _to_summary(saved)
