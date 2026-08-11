from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum


class WithdrawalStatus(StrEnum):
    """인출 상태 — BOUNDARIES §3 2단계 흐름.

    REQUESTED ──이체 완료──▶ PAID
        └──── 이체 실패 ───▶ FAILED (잔액 복원 기입과 원자적)
    """

    REQUESTED = "REQUESTED"
    PAID = "PAID"
    FAILED = "FAILED"


class InvalidWithdrawalStateError(Exception):
    """현재 상태에서 허용되지 않는 전이."""


def compute_withholding_tax(amount_krw: int, tax_permille: int) -> int:
    """원천징수 세액 — 사업소득 3.3%(=33‰), 정수 원 단위 내림."""
    return amount_krw * tax_permille // 1000


@dataclass(frozen=True, slots=True)
class Withdrawal:
    """인출 요청 도메인 엔티티 — 계좌 정보는 요청 시점 스냅샷(이력 보존)."""

    id: int
    user_id: int
    amount_krw: int  # 잔액에서 차감된 총액
    tax_krw: int  # 원천징수 세액(플랫폼이 대리 신고·납부)
    payout_krw: int  # 실지급액 = amount - tax
    bank_name: str
    account_number: str
    account_holder: str
    status: WithdrawalStatus
    created_at: datetime | None = None
    settled_at: datetime | None = None

    def mark_paid(self) -> Withdrawal:
        """이체 완료 확정 — 요청 상태에서만."""
        if self.status is not WithdrawalStatus.REQUESTED:
            raise InvalidWithdrawalStateError(f"이미 처리된 인출입니다: {self.status.value}")
        return replace(self, status=WithdrawalStatus.PAID)

    def mark_failed(self) -> Withdrawal:
        """이체 실패 — 요청 상태에서만. 잔액 복원 기입은 리포지토리가 원자적으로 수행."""
        if self.status is not WithdrawalStatus.REQUESTED:
            raise InvalidWithdrawalStateError(f"이미 처리된 인출입니다: {self.status.value}")
        return replace(self, status=WithdrawalStatus.FAILED)
