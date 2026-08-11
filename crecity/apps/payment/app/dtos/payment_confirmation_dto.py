from dataclasses import dataclass


@dataclass(frozen=True)
class ConfirmCommand:

    payment_key: str
    pg_order_id: str
    amount_krw: int  # 리다이렉트 쿼리의 amount — 서버 확정값과 대조
    requester_user_id: int


@dataclass(frozen=True)
class ConfirmResult:

    order_id: int  # 생성된 주문(장바구니는 첫 주문) — 프론트는 주문 상세로 이동
    order_ids: tuple[int, ...] = ()  # 장바구니 결제 시 생성된 전체 주문 — 단건은 빈 튜플
