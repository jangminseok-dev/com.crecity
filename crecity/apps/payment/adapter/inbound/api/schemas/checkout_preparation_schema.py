from pydantic import BaseModel, Field


class CheckoutRequestSchema(BaseModel):

    package_id: int
    requirements: str = Field(..., description="브랜드 요구사항 — 주문 생성 시 그대로 사용")


class CheckoutResponseSchema(BaseModel):
    """토스 결제창(SDK v2) 호출 파라미터 — amount는 서버 확정값."""

    pg_order_id: str
    amount_krw: int
    order_name: str
    client_key: str
