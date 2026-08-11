from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class LedgerEntryType(StrEnum):
    """원장 기입 유형 — append-only 저널(BOUNDARIES §3: 원장은 order 소유).

    ESCROW_DEPOSIT      주문 생성 시 브랜드 결제액 예치 기록(잔액 영향 없음 — 감사용)
    BRAND_CREDIT_REFUND 거절·만료 환불 → 브랜드 크레딧 적립(+)
    CREATOR_EARNING     구매 확정 → 크리에이터 잔액 적립(+)
    PLATFORM_REVENUE    구매 확정 시 플랫폼 수수료 몫(user_id 없음)
    """

    ESCROW_DEPOSIT = "ESCROW_DEPOSIT"
    BRAND_CREDIT_REFUND = "BRAND_CREDIT_REFUND"
    CREATOR_EARNING = "CREATOR_EARNING"
    PLATFORM_REVENUE = "PLATFORM_REVENUE"
    # 인출(BOUNDARIES §3) — 요청 시 차감, 이체 실패 시 복원
    WITHDRAWAL = "WITHDRAWAL"
    WITHDRAWAL_REVERSAL = "WITHDRAWAL_REVERSAL"


# 사용자 잔액으로 합산되는 기입 유형(적립성)
BALANCE_CREDIT_TYPES = frozenset(
    {
        LedgerEntryType.BRAND_CREDIT_REFUND,
        LedgerEntryType.CREATOR_EARNING,
        LedgerEntryType.WITHDRAWAL_REVERSAL,
    }
)

# 잔액에서 빼는 기입 유형(차감성) — 잔액 = 적립 합 − 차감 합
BALANCE_DEBIT_TYPES = frozenset({LedgerEntryType.WITHDRAWAL})


@dataclass(frozen=True, slots=True)
class LedgerEntryDraft:
    """전이가 만들어낸 기입 초안 — 주문 전이와 같은 트랜잭션으로 저장돼야 한다."""

    entry_type: LedgerEntryType
    user_id: int | None  # PLATFORM_REVENUE는 None
    amount_krw: int


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    """저장된 원장 기입 — 수정·삭제 없는 append-only.

    출처는 order_id(주문 전이) 또는 withdrawal_id(인출) 중 하나다.
    """

    id: int
    order_id: int | None
    entry_type: LedgerEntryType
    user_id: int | None
    amount_krw: int
    withdrawal_id: int | None = None
    created_at: datetime | None = None
