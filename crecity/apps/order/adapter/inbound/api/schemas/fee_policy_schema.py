from __future__ import annotations

from pydantic import BaseModel

from order.app.dtos.fee_policy_dto import FeePolicyResult


class FeePolicyResponseSchema(BaseModel):

    brand_fee_percent: int
    creator_fee_percent: int
    withdrawal_tax_permille: int  # 33 = 3.3%
    response_deadline_hours: int

    @classmethod
    def from_result(cls, result: FeePolicyResult) -> FeePolicyResponseSchema:
        return cls(
            brand_fee_percent=result.brand_fee_percent,
            creator_fee_percent=result.creator_fee_percent,
            withdrawal_tax_permille=result.withdrawal_tax_permille,
            response_deadline_hours=result.response_deadline_hours,
        )
