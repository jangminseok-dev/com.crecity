from dataclasses import dataclass


@dataclass(frozen=True)
class MyOrdersQuery:

    user_id: int  # 브랜드·크리에이터 어느 쪽 참여든 조회


@dataclass(frozen=True)
class OrderDetailQuery:

    order_id: int
    requester_user_id: int  # 당사자만 조회 가능
