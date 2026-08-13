from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from order.domain.entities.withdrawal_entity import Withdrawal
from order.domain.value_objects.annual_payout import AnnualPayout


@dataclass(frozen=True)
class StatementQuery:
    user_id: int
    year: int


@dataclass(frozen=True)
class PayoutItem:
    """명세서 한 줄 — 지급 건별 내역."""

    withdrawal_id: int
    amount_krw: int
    tax_krw: int
    payout_krw: int
    settled_at: datetime | None

    @classmethod
    def from_withdrawal(cls, withdrawal: Withdrawal) -> PayoutItem:
        return cls(
            withdrawal_id=withdrawal.id,
            amount_krw=withdrawal.amount_krw,
            tax_krw=withdrawal.tax_krw,
            payout_krw=withdrawal.payout_krw,
            settled_at=withdrawal.settled_at,
        )


@dataclass(frozen=True)
class StatementResult:
    """연간 지급명세서 — 합계 + 건별 내역."""

    year: int
    user_id: int
    count: int
    total_amount_krw: int
    total_tax_krw: int
    total_payout_krw: int
    items: list[PayoutItem]

    @classmethod
    def of(cls, year: int, summary: AnnualPayout, withdrawals: list[Withdrawal]) -> StatementResult:
        return cls(
            year=year,
            user_id=summary.user_id,
            count=summary.count,
            total_amount_krw=summary.total_amount_krw,
            total_tax_krw=summary.total_tax_krw,
            total_payout_krw=summary.total_payout_krw,
            items=[PayoutItem.from_withdrawal(w) for w in withdrawals],
        )
