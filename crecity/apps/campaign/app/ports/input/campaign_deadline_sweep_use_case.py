from __future__ import annotations

from abc import ABC, abstractmethod

from campaign.app.dtos.campaign_deadline_sweep_dto import CampaignSweepResult


class CampaignDeadlineSweepUseCase(ABC):
    """공고 마감일 스캔(§3.2, 갭 #27) — cron이 주기 실행한다(HTTP 표면 없음)."""

    @abstractmethod
    async def sweep(self) -> CampaignSweepResult:
        """마감일이 지난 OPEN 공고를 CLOSED로 전이한다."""
        ...
