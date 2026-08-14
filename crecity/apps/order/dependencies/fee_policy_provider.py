from __future__ import annotations

from core.config import (
    ORDER_BRAND_FEE_PERCENT,
    ORDER_CREATOR_FEE_PERCENT,
    ORDER_RESPONSE_DEADLINE_HOURS,
    WITHDRAWAL_TAX_PERMILLE,
)
from order.app.ports.input.fee_policy_use_case import FeePolicyUseCase
from order.app.use_cases.fee_policy_interactor import FeePolicyInteractor


def get_fee_policy_use_case() -> FeePolicyUseCase:
    return FeePolicyInteractor(
        brand_fee_percent=ORDER_BRAND_FEE_PERCENT,
        creator_fee_percent=ORDER_CREATOR_FEE_PERCENT,
        withdrawal_tax_permille=WITHDRAWAL_TAX_PERMILLE,
        response_deadline_hours=ORDER_RESPONSE_DEADLINE_HOURS,
    )
