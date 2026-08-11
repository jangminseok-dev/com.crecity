from pydantic import BaseModel, Field


class CheckoutRequestSchema(BaseModel):

    package_id: int
    requirements: str = Field(..., description="브랜드 요구사항 — 주문 생성 시 그대로 사용")
    use_credit: bool = Field(False, description="보유 크레딧 사용 여부 — 적용액은 서버가 확정")


class OfferCheckoutRequestSchema(BaseModel):

    offer_id: int
    requirements: str = Field(..., description="브랜드 요구사항 — 주문 생성 시 그대로 사용")
    use_credit: bool = Field(False, description="보유 크레딧 사용 여부 — 적용액은 서버가 확정")


class ApplicationCheckoutRequestSchema(BaseModel):

    application_id: int
    requirements: str = Field(..., description="브랜드 요구사항 — 주문 생성 시 그대로 사용")
    use_credit: bool = Field(False, description="보유 크레딧 사용 여부 — 적용액은 서버가 확정")


class CheckoutResponseSchema(BaseModel):
    """토스 결제창(SDK v2) 호출 파라미터 — 금액은 서버 확정값.

    pg_amount_krw가 0이면(전액 크레딧) 결제창 없이 바로 /payment/confirm으로 간다.
    """

    pg_order_id: str
    amount_krw: int  # 결제 총액(크레딧 포함 전체)
    credit_applied_krw: int
    pg_amount_krw: int  # 결제창 청구액 = amount_krw − credit_applied_krw
    order_name: str
    client_key: str
