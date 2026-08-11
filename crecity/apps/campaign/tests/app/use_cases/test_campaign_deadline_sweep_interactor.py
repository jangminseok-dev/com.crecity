from datetime import datetime, timedelta, timezone

from campaign.app.use_cases.campaign_deadline_sweep_interactor import (
    CampaignDeadlineSweepInteractor,
)
from campaign.domain.entities.campaign_entity import (
    Campaign,
    CampaignPlatform,
    CampaignStatus,
)

_NOW = datetime.now(timezone.utc)
BRAND = 100


class _StubCampaignRepository:
    def __init__(self, expired: list[Campaign]):
        self.expired = expired
        self.status_updates = []

    async def create(self, **kwargs):
        raise NotImplementedError

    async def find_by_id(self, campaign_id):
        raise NotImplementedError

    async def update_status(self, campaign_id, status):
        self.status_updates.append((campaign_id, status))

    async def list_by_status(self, status, limit, offset):
        raise NotImplementedError

    async def list_by_brand(self, brand_user_id):
        raise NotImplementedError

    async def find_expired(self, now, limit):
        return self.expired


def _campaign(campaign_id=1, status=CampaignStatus.OPEN, deadline_at=_NOW - timedelta(hours=1)):
    return Campaign(
        id=campaign_id, brand_user_id=BRAND, title="신제품 릴스 캠페인",
        description="설명", platform=CampaignPlatform.INSTAGRAM, budget_krw=500000,
        status=status, deadline_at=deadline_at,
    )


async def test_마감일이_지난_공고는_자동_마감된다():
    repository = _StubCampaignRepository([_campaign(1), _campaign(2)])
    result = await CampaignDeadlineSweepInteractor(repository).sweep()
    assert result.closed_campaign_ids == [1, 2]
    assert repository.status_updates == [(1, CampaignStatus.CLOSED), (2, CampaignStatus.CLOSED)]


async def test_이미_마감된_공고는_건너뛴다():
    repository = _StubCampaignRepository([_campaign(1, status=CampaignStatus.CLOSED)])
    result = await CampaignDeadlineSweepInteractor(repository).sweep()
    assert result.closed_campaign_ids == []
    assert repository.status_updates == []


async def test_마감_대상이_없으면_아무_일도_없다():
    repository = _StubCampaignRepository([])
    result = await CampaignDeadlineSweepInteractor(repository).sweep()
    assert result.closed_campaign_ids == []
