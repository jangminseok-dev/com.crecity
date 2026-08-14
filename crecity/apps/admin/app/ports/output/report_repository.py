from __future__ import annotations

from abc import ABC, abstractmethod

from admin.domain.entities.report_entity import Report, ReportTargetType


class ReportRepository(ABC):
    """신고 영속성 포트(갭 #54) — 접수·조회·처리."""

    @abstractmethod
    async def create(
        self,
        reporter_user_id: int,
        target_type: ReportTargetType,
        target_id: int,
        reason: str,
    ) -> Report: ...

    @abstractmethod
    async def find_by_id(self, report_id: int) -> Report | None: ...

    @abstractmethod
    async def exists_open_by_reporter(
        self, reporter_user_id: int, target_type: ReportTargetType, target_id: int
    ) -> bool:
        """같은 사람이 같은 대상에 대해 처리 대기 중인 신고를 이미 냈는지(중복 접수 차단)."""
        ...

    @abstractmethod
    async def list_open(self, limit: int) -> list[Report]:
        """처리 대기 신고 — 오래된 순(먼저 들어온 것부터 본다)."""
        ...

    @abstractmethod
    async def resolve(
        self, report_id: int, resolver_user_id: int, note: str
    ) -> Report | None: ...
