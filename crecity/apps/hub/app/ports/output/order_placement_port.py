from __future__ import annotations

from abc import ABC, abstractmethod

from hub.app.dtos.placed_order_dto import PlacedOrder


class OrderPlacementPort(ABC):
    """결제 완료 주문 생성 포트 — 구현은 order가 제공하고 main.py가 조립한다.

    §3 결제 흐름: payment가 PG 승인 → 이 포트로 주문 생성+예치(원자적).
    expected_brand_total_krw가 현재 계산과 다르면(결제 사이 가격 변동) 생성하지 않고
    None을 돌려준다 — payment는 PG 취소로 보정한다.
    """

    @abstractmethod
    async def place_paid_order(
        self,
        package_id: int,
        requirements: str,
        brand_user_id: int,
        expected_brand_total_krw: int,
    ) -> PlacedOrder | None:
        """주문 생성 — 패키지 불가·금액 불일치·생성 실패면 None."""
        ...

    @abstractmethod
    async def place_paid_custom_order(
        self,
        offer_id: int,
        requirements: str,
        brand_user_id: int,
        expected_brand_total_krw: int,
    ) -> PlacedOrder | None:
        """커스텀 오퍼 주문 생성 — 오퍼 불가·금액 불일치·생성 실패면 None."""
        ...
