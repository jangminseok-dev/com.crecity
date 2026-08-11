from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum


class AdjustmentStatus(StrEnum):
    """금액 변경 요청 상태 — 수락은 곧 추가 결제다(에스크로 무결성, §3.8·§6)."""

    REQUESTED = "REQUESTED"  # 브랜드 응답 대기
    PAID = "PAID"  # 브랜드가 추가 결제 완료 → 주문 금액 증액됨
    DECLINED = "DECLINED"  # 브랜드 거절


class InvalidAdjustmentError(Exception):
    """이미 처리된 요청·권한 없는 처리 — 라우터에서 409/403으로 변환."""


@dataclass(frozen=True, slots=True)
class OrderAdjustment:
    """진행 중 주문의 추가 금액 요청 — 크리에이터가 범위 확대를 청구한다.

    감액은 취급하지 않는다(이미 예치된 에스크로를 건드리므로 합의 취소로 처리).
    """

    id: int
    order_id: int
    extra_amount_krw: int  # 추가 금액(양수)
    reason: str
    status: AdjustmentStatus
    created_at: datetime | None = None

    def is_payable(self) -> bool:
        return self.status is AdjustmentStatus.REQUESTED

    def decline(self) -> OrderAdjustment:
        if not self.is_payable():
            raise InvalidAdjustmentError("이미 처리된 요청입니다.")
        return replace(self, status=AdjustmentStatus.DECLINED)

    def mark_paid(self) -> OrderAdjustment:
        if not self.is_payable():
            raise InvalidAdjustmentError("이미 처리된 요청입니다.")
        return replace(self, status=AdjustmentStatus.PAID)
