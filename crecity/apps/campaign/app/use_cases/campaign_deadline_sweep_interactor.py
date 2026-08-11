from __future__ import annotations

from datetime import datetime, timezone

from campaign.app.dtos.campaign_deadline_sweep_dto import CampaignSweepResult
from campaign.app.ports.input.campaign_deadline_sweep_use_case import (
    CampaignDeadlineSweepUseCase,
)
from campaign.app.ports.output.campaign_repository import CampaignRepository

# 1회 스캔 상한 — 밀린 만료가 많아도 한 번에 다 처리하지 않는다(다음 주기가 이어받음)
_SWEEP_BATCH_LIMIT = 100


class CampaignDeadlineSweepInteractor(CampaignDeadlineSweepUseCase):

    def __init__(self, campaigns: CampaignRepository) -> None:
        self._campaigns = campaigns

    async def sweep(self) -> CampaignSweepResult:
        now = datetime.now(timezone.utc)
        expired = await self._campaigns.find_expired(now, limit=_SWEEP_BATCH_LIMIT)
        closed_ids: list[int] = []
        for campaign in expired:
            updated = campaign.expire(now)
            if updated is None:  # 경합으로 이미 마감된 경우 등
                continue
            await self._campaigns.update_status(updated.id, updated.status)
            closed_ids.append(updated.id)
        return CampaignSweepResult(closed_campaign_ids=closed_ids)
