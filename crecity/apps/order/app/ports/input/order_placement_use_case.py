from __future__ import annotations

from abc import ABC, abstractmethod

from order.app.dtos.order_placement_dto import (
    CustomOrderPlacementCommand,
    OrderPlacementCommand,
)
from order.app.dtos.order_result_dto import OrderResult


class OrderPlacementUseCase(ABC):
    """주문 생성 유스케이스 — 브랜드가 패키지를 주문한다.

    금액·수수료율은 이 시점에 스냅샷되고(§7-4) 에스크로 예치가 원장에 기록된다.
    PG 결제(pay-in)는 payment 앱 도입 시 이 앞단에 붙는다(BOUNDARIES §3).
    """

    @abstractmethod
    async def place(self, command: OrderPlacementCommand) -> OrderResult:
        """주문을 생성한다 — 72h 수락 마감과 함께 PENDING_ACCEPT로 시작.

        Raises:
            NotBrandAccountError: 브랜드 계정이 아님.
            PackageNotOrderableError: 패키지가 없거나 주문 불가.
        """
        ...

    @abstractmethod
    async def place_custom(self, command: CustomOrderPlacementCommand) -> OrderResult:
        """커스텀 오퍼 주문 생성 — 가격·당사자는 허브 CustomOfferPort로 해석한다.

        Raises:
            NotBrandAccountError: 브랜드 계정이 아니거나 오퍼 수신 브랜드가 아님.
            PackageNotOrderableError: 오퍼가 없거나 이미 결제됨.
        """
        ...
