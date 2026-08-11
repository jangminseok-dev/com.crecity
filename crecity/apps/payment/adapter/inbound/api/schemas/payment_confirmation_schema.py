from pydantic import BaseModel, Field


class ConfirmRequestSchema(BaseModel):
    """토스 successUrl 리다이렉트 쿼리(paymentKey·orderId·amount)를 그대로 전달받는다.

    전액 크레딧 결제(PG 결제액 0)는 결제창을 거치지 않으므로 payment_key가 빈 문자열,
    amount_krw가 0으로 들어온다.
    """

    payment_key: str = Field("", description="PG 결제 키 — 전액 크레딧 결제는 빈 문자열")
    pg_order_id: str
    amount_krw: int = Field(..., description="리다이렉트 쿼리의 amount(PG 청구액) — 서버 확정값과 대조됨")


class ConfirmResponseSchema(BaseModel):

    order_id: int
