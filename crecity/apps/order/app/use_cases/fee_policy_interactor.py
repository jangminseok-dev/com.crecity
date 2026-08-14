from __future__ import annotations

from order.app.dtos.fee_policy_dto import FeePolicyResult
from order.app.ports.input.fee_policy_use_case import FeePolicyUseCase


class FeePolicyInteractor(FeePolicyUseCase):
    """설정값을 그대로 전달한다 — I/O가 없으므로 def(동기)."""

    def __init__(
        self,
        brand_fee_percent: int,
        creator_fee_percent: int,
        withdrawal_tax_permille: int,
        response_deadline_hours: int,
    ) -> None:
        self._policy = FeePolicyResult(
            brand_fee_percent=brand_fee_percent,
            creator_fee_percent=creator_fee_percent,
            withdrawal_tax_permille=withdrawal_tax_permille,
            response_deadline_hours=response_deadline_hours,
        )

    def get_policy(self) -> FeePolicyResult:
        return self._policy
