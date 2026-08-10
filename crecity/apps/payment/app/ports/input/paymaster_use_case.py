from __future__ import annotations

from abc import ABC, abstractmethod

from payment.app.dtos.paymaster_dto import PaymasterQuery, PaymasterResponse


class PaymasterUseCase(ABC):
    """결제 (payment) 유스케이스 — 외부 결제 접점(PG) 담당."""

    @abstractmethod
    async def introduce_myself(self, query: PaymasterQuery) -> PaymasterResponse:
        """결제 (payment)의 자기소개 메소드."""
        ...
