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


# 사용자 잔액으로 합산되는 기입 유형(적립성) — 추후 인출·크레딧 사용이 차감 유형으로 추가된다
BALANCE_CREDIT_TYPES = frozenset(
    {LedgerEntryType.BRAND_CREDIT_REFUND, LedgerEntryType.CREATOR_EARNING}
)


@dataclass(frozen=True, slots=True)
class LedgerEntryDraft:
    """전이가 만들어낸 기입 초안 — 주문 전이와 같은 트랜잭션으로 저장돼야 한다."""

    entry_type: LedgerEntryType
    user_id: int | None  # PLATFORM_REVENUE는 None
    amount_krw: int


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    """저장된 원장 기입 — 수정·삭제 없는 append-only."""

    id: int
    order_id: int
    entry_type: LedgerEntryType
    user_id: int | None
    amount_krw: int
    created_at: datetime | None = None
