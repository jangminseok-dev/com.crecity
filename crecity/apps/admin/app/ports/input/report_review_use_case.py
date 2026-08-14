from __future__ import annotations

from abc import ABC, abstractmethod

from admin.app.dtos.report_dto import ReportResolveCommand, ReportResult


class ReportReviewUseCase(ABC):
    """신고 처리(갭 #54) — 운영자가 대기 목록을 보고 처리 메모를 남기며 닫는다."""

    @abstractmethod
    async def list_reports(self, resolved: bool = False) -> list[ReportResult]:
        """resolved면 처리 완료 이력(갭 #71), 아니면 처리 대기 목록."""
        ...

    @abstractmethod
    async def resolve(self, command: ReportResolveCommand) -> ReportResult: ...
