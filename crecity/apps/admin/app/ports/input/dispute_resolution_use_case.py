from __future__ import annotations

from abc import ABC, abstractmethod

from admin.app.dtos.dispute_resolution_dto import DisputeDecisionCommand
from hub.app.dtos.dispute_resolution_dto import DisputeSummary


class DisputeResolutionUseCase(ABC):
    """분쟁 중재 — 대기 목록 조회와 판정(감사 기록 포함)."""

    @abstractmethod
    async def list_open(self) -> list[DisputeSummary]: ...

    @abstractmethod
    async def resolve(self, command: DisputeDecisionCommand) -> DisputeSummary: ...
