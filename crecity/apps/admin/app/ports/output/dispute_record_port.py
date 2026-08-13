from __future__ import annotations

from abc import ABC, abstractmethod


class DisputeRecordPort(ABC):
    """분쟁 판정 감사 기록 아웃바운드 포트 — 공용 PG 어댑터가 subject로 구분해 쌓는다."""

    @abstractmethod
    async def record(self, subject: str, note: str) -> None: ...
