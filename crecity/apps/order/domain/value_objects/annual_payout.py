from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from order.domain.entities.withdrawal_entity import Withdrawal


@dataclass(frozen=True, slots=True)
class AnnualPayout:
    """연간 지급 집계 — 지급명세서(원천징수영수증)의 합계란.

    지급일(`settled_at`) 기준으로 실제 지급 완료(PAID)된 인출만 센다.
    """

    user_id: int
    count: int
    total_amount_krw: int  # 지급 총액(세전)
    total_tax_krw: int  # 원천징수 세액 합
    total_payout_krw: int  # 실지급액 합

    @classmethod
    def of(cls, user_id: int, withdrawals: list[Withdrawal]) -> AnnualPayout:
        return cls(
            user_id=user_id,
            count=len(withdrawals),
            total_amount_krw=sum(w.amount_krw for w in withdrawals),
            total_tax_krw=sum(w.tax_krw for w in withdrawals),
            total_payout_krw=sum(w.payout_krw for w in withdrawals),
        )
