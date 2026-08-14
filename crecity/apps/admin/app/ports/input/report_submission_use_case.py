from __future__ import annotations

from abc import ABC, abstractmethod

from admin.app.dtos.report_dto import ReportResult, ReportSubmissionCommand


class ReportSubmissionUseCase(ABC):
    """어뷰징 신고 접수(갭 #54) — 로그인 사용자면 누구나 낸다."""

    @abstractmethod
    async def submit(self, command: ReportSubmissionCommand) -> ReportResult: ...
