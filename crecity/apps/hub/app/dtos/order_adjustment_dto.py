from dataclasses import dataclass


@dataclass(frozen=True)
class OrderAdjustmentSummary:
    """결제 가능한 주문 금액 변경 요청 요약 — order가 채워 준다(갭 #31)."""

    adjustment_id: int
    order_id: int
    order_title: str  # 결제창 표시용
    extra_amount_krw: int  # 추가 금액(수수료 별도)
    brand_user_id: int  # 이 브랜드만 결제 가능
