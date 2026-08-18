from __future__ import annotations

from abc import ABC, abstractmethod

from hub.app.dtos.completed_order_price_dto import PackageOrderAmount


class CompletedOrderPricePort(ABC):
    """완료 주문 실거래가 포트(갭 #89) — 구현은 order가 제공한다.

    거래가는 order 소유이므로 creator(시세 집계)는 이 계약으로만 읽는다.
    패키지 없는 주문(커스텀 오퍼)은 분류할 수 없어 제외된다.
    """

    @abstractmethod
    async def list_completed_package_amounts(self) -> list[PackageOrderAmount]: ...
