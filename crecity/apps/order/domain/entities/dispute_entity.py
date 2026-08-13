from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum


class DisputeStatus(StrEnum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class DisputeResolution(StrEnum):
    """운영자 판정 — 부분 배분은 지원하지 않는다(전액 환불 또는 전액 지급).

    REFUND   브랜드에게 전액 환불(크레딧) — 주문 취소
    RELEASE  크리에이터에게 전액 지급 — 구매 확정과 동일
    DISMISS  기각 — 주문 상태를 바꾸지 않고 분쟁만 닫는다(이미 종료된 주문 포함)
    """

    REFUND = "REFUND"
    RELEASE = "RELEASE"
    DISMISS = "DISMISS"


class InvalidDisputeStateError(Exception):
    """이미 처리된 분쟁에 대한 판정 — 라우터에서 409로 변환."""


@dataclass(frozen=True, slots=True)
class Dispute:
    """분쟁 — 당사자가 신고하고 운영자가 판정한다(collabstr §3.8 지원팀 중재).

    판정 전까지 주문은 그대로 유지되며, 검토 마감 자동 승인은 보류된다.
    """

    id: int
    order_id: int
    raised_by_user_id: int
    reason: str
    status: DisputeStatus
    resolution: DisputeResolution | None = None
    resolved_by_user_id: int | None = None  # 판정한 운영자
    created_at: datetime | None = None
    resolved_at: datetime | None = None

    def resolve(
        self, resolution: DisputeResolution, operator_user_id: int, now: datetime
    ) -> Dispute:
        if self.status is not DisputeStatus.OPEN:
            raise InvalidDisputeStateError(f"이미 처리된 분쟁입니다: {self.id}")
        return replace(
            self,
            status=DisputeStatus.RESOLVED,
            resolution=resolution,
            resolved_by_user_id=operator_user_id,
            resolved_at=now,
        )
