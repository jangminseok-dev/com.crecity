from __future__ import annotations

from abc import ABC, abstractmethod


class SettlementRecordPort(ABC):
    """인출 처리 감사 기록 아웃바운드 포트 — 지금은 로그, 감사 테이블 필요 시 PG로 교체."""

    @abstractmethod
    async def record(self, subject: str, note: str) -> None: ...
