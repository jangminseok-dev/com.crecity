from dataclasses import dataclass


@dataclass(frozen=True)
class DisputeDecisionCommand:

    dispute_id: int
    resolution: str  # REFUND(브랜드 전액 환불) | RELEASE(크리에이터 전액 지급) | DISMISS(기각)
    operator_id: int
    operator_email: str
