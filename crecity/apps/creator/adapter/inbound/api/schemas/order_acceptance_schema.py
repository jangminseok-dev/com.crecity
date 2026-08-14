from __future__ import annotations

from pydantic import BaseModel

from creator.app.dtos.order_acceptance_dto import OrderAcceptanceResult


class OrderAcceptanceRequestSchema(BaseModel):

    accepting: bool


class OrderAcceptanceResponseSchema(BaseModel):

    slug: str
    accepting_orders: bool

    @classmethod
    def from_result(cls, result: OrderAcceptanceResult) -> OrderAcceptanceResponseSchema:
        return cls(slug=result.slug, accepting_orders=result.accepting_orders)
