from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DisputeSummary:
    """운영 판정용 분쟁 요약 — order가 소유한 분쟁을 admin이 처리할 때의 계약.

    판정 근거로 주문의 금액·당사자·상태를 함께 싣는다(운영자가 별도 조회 없이 판단).
    """

    id: int
    order_id: int
    package_title: str
    brand_user_id: int
    creator_user_id: int
    amount_krw: int
    brand_total_krw: int
    order_status: str
    raised_by_user_id: int
    reason: str
    status: str  # OPEN | RESOLVED
    resolution: str | None  # REFUND | RELEASE | DISMISS
    created_at: datetime | None
