from dataclasses import dataclass


@dataclass(frozen=True)
class PlacedOrder:
    """결제 승인 후 생성된 주문 요약 — payment → order 허브 계약(BOUNDARIES §3)."""

    id: int
    brand_total_krw: int  # 에스크로 예치액(결제 금액과 일치해야 한다)
