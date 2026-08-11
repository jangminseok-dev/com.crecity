from __future__ import annotations

from abc import ABC, abstractmethod

from payment.domain.entities.payment_intent_entity import PaymentIntent


class PaymentIntentRepository(ABC):
    """결제 의도 영속성 포트 — 시도·결과를 전부 기록한다(외부 접점 감사 근거)."""

    @abstractmethod
    async def create(
        self,
        pg_order_id: str,
        package_id: int | None,
        brand_user_id: int,
        requirements: str,
        amount_krw: int,
        offer_id: int | None = None,
        application_id: int | None = None,
        adjustment_id: int | None = None,
        credit_applied_krw: int = 0,
        cart_package_ids: list[int] | None = None,
    ) -> PaymentIntent: ...

    @abstractmethod
    async def find_by_pg_order_id(self, pg_order_id: str) -> PaymentIntent | None: ...

    @abstractmethod
    async def mark_confirmed(self, intent_id: int, payment_key: str, order_id: int) -> None: ...

    @abstractmethod
    async def mark_failed(self, intent_id: int, payment_key: str | None, reason: str) -> None: ...
