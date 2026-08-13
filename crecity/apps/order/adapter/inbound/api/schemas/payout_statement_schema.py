from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from order.app.dtos.payout_statement_dto import StatementResult


class PayoutItemSchema(BaseModel):
    withdrawal_id: int
    amount_krw: int
    tax_krw: int
    payout_krw: int
    settled_at: datetime | None


class PayoutStatementSchema(BaseModel):
    year: int
    user_id: int
    count: int
    total_amount_krw: int
    total_tax_krw: int
    total_payout_krw: int
    items: list[PayoutItemSchema]

    @classmethod
    def from_result(cls, result: StatementResult) -> PayoutStatementSchema:
        return cls(
            year=result.year,
            user_id=result.user_id,
            count=result.count,
            total_amount_krw=result.total_amount_krw,
            total_tax_krw=result.total_tax_krw,
            total_payout_krw=result.total_payout_krw,
            items=[
                PayoutItemSchema(
                    withdrawal_id=item.withdrawal_id,
                    amount_krw=item.amount_krw,
                    tax_krw=item.tax_krw,
                    payout_krw=item.payout_krw,
                    settled_at=item.settled_at,
                )
                for item in result.items
            ],
        )
