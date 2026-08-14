from __future__ import annotations

from abc import ABC, abstractmethod


class ReportRecordPort(ABC):
    """신고 처리 감사 기록 아웃바운드 포트(갭 #54) — 누가 어떤 신고를 닫았는지 남긴다."""

    @abstractmethod
    async def record(self, subject: str, note: str) -> None: ...
