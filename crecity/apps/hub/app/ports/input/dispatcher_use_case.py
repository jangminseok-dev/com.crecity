from __future__ import annotations

from abc import ABC, abstractmethod

from hub.app.dtos.dispatcher_dto import DispatcherQuery, DispatcherResponse


class DispatcherUseCase(ABC):
    """허브 (hub) 유스케이스 — 앱 간 협력의 단일 교차점 — 계약(포트·DTO)만 소유."""

    @abstractmethod
    async def introduce_myself(self, query: DispatcherQuery) -> DispatcherResponse:
        """허브 (hub)의 자기소개 메소드."""
        ...
