from dataclasses import dataclass


@dataclass(frozen=True)
class OrderParticipants:
    """주문 당사자·상태 요약 — review → order 허브 계약(리뷰 자격 검증용)."""

    order_id: int
    status: str  # OrderStatus 값 문자열
    brand_user_id: int
    creator_user_id: int
