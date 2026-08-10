from pydantic import BaseModel, Field


class ConfirmRequestSchema(BaseModel):
    """토스 successUrl 리다이렉트 쿼리(paymentKey·orderId·amount)를 그대로 전달받는다."""

    payment_key: str
    pg_order_id: str
    amount_krw: int = Field(..., description="리다이렉트 쿼리의 amount — 서버 확정값과 대조됨")


class ConfirmResponseSchema(BaseModel):

    order_id: int
