from dataclasses import dataclass


@dataclass(frozen=True)
class SettlementDecisionCommand:

    withdrawal_id: int
    completed: bool  # True=이체 완료 확정 / False=이체 실패(잔액 복원)
    operator_id: int
    operator_email: str
