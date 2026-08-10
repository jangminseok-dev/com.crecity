from __future__ import annotations

from abc import ABC, abstractmethod

from admin.app.dtos.steward_dto import StewardQuery, StewardResponse


class StewardUseCase(ABC):
    """운영 (admin) 유스케이스 — 심사·중재·운영 담당."""

    @abstractmethod
    async def introduce_myself(self, query: StewardQuery) -> StewardResponse:
        """운영 (admin)의 자기소개 메소드."""
        ...
