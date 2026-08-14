from __future__ import annotations

from abc import ABC, abstractmethod

from creator.app.dtos.profile_view_dto import DailyView


class ProfileViewRepository(ABC):
    """조회수 집계 영속성 포트(갭 #57)."""

    @abstractmethod
    async def increment(self, profile_id: int) -> None:
        """오늘 행을 UPSERT로 1 증가 — 동시 조회에서도 유실되지 않는다."""
        ...

    @abstractmethod
    async def list_recent(self, profile_id: int, days: int) -> list[DailyView]:
        """최근 days일 일별 집계 — 조회가 없던 날은 행이 없다(호출 측이 0으로 채운다)."""
        ...
