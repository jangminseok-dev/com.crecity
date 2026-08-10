from dataclasses import dataclass


@dataclass(frozen=True)
class ConfirmCommand:

    payment_key: str
    pg_order_id: str
    amount_krw: int  # 리다이렉트 쿼리의 amount — 서버 확정값과 대조
    requester_user_id: int


@dataclass(frozen=True)
class ConfirmResult:

    order_id: int  # 생성된 주문 — 프론트는 주문 상세로 이동
