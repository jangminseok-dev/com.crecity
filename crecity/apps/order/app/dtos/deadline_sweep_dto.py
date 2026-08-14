from dataclasses import dataclass


@dataclass(frozen=True)
class SweepOutcome:

    order_id: int
    status: str  # 전이 결과 — REFUNDED(수락 만료) | COMPLETED(검토 만료)


@dataclass(frozen=True)
class SweepResult:

    outcomes: list[SweepOutcome]
    warned_order_ids: list[int] | None = None  # 마감 임박을 알린 주문(갭 #76)
