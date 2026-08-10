from dataclasses import dataclass


@dataclass(frozen=True)
class SweepOutcome:

    order_id: int
    status: str  # 전이 결과 — REFUNDED(수락 만료) | COMPLETED(검토 만료)


@dataclass(frozen=True)
class SweepResult:

    outcomes: list[SweepOutcome]
