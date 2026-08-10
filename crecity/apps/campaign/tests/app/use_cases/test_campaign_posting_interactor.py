import pytest

from campaign.app.dtos.campaign_posting_dto import CloseCampaignCommand, PostCampaignCommand
from campaign.app.exceptions import CampaignNotFoundError, NotBrandAccountError
from campaign.app.use_cases.campaign_posting_interactor import CampaignPostingInteractor
from campaign.domain.entities.campaign_entity import (
    Campaign,
    CampaignPlatform,
    CampaignStatus,
    InvalidCampaignStateError,
    NotCampaignOwnerError,
)

BRAND = 100


class _StubCampaignRepository:
    def __init__(self, campaign: Campaign | None = None):
        self.campaign = campaign
        self.created = []
        self.status_updates = []

    async def create(self, brand_user_id, title, description, platform, budget_krw):
        campaign = Campaign(
            id=1, brand_user_id=brand_user_id, title=title, description=description,
            platform=platform, budget_krw=budget_krw, status=CampaignStatus.OPEN,
        )
        self.created.append(campaign)
        return campaign

    async def find_by_id(self, campaign_id):
        return self.campaign if self.campaign and self.campaign.id == campaign_id else None

    async def update_status(self, campaign_id, status):
        self.status_updates.append((campaign_id, status))

    async def list_by_status(self, status, limit, offset):
        raise NotImplementedError

    async def list_by_brand(self, brand_user_id):
        raise NotImplementedError


def _campaign(status=CampaignStatus.OPEN):
    return Campaign(
        id=1, brand_user_id=BRAND, title="신제품 릴스", description="설명",
        platform=CampaignPlatform.INSTAGRAM, budget_krw=500000, status=status,
    )


def _post_command(account_type="BRAND", platform="INSTAGRAM", budget=500000):
    return PostCampaignCommand(
        title="신제품 릴스", description="신제품 소개 릴스 제작", platform=platform,
        budget_krw=budget, brand_user_id=BRAND, account_type=account_type,
    )


async def test_브랜드가_공고를_올리면_OPEN으로_시작한다():
    repo = _StubCampaignRepository()
    result = await CampaignPostingInteractor(repo).post(_post_command())
    assert result.status == "OPEN"
    assert repo.created[0].platform is CampaignPlatform.INSTAGRAM


async def test_크리에이터_계정이면_NotBrandAccountError():
    with pytest.raises(NotBrandAccountError):
        await CampaignPostingInteractor(_StubCampaignRepository()).post(
            _post_command(account_type="CREATOR")
        )


async def test_잘못된_플랫폼_예산이면_ValueError():
    interactor = CampaignPostingInteractor(_StubCampaignRepository())
    with pytest.raises(ValueError):
        await interactor.post(_post_command(platform="FACEBOOK"))
    with pytest.raises(ValueError):
        await interactor.post(_post_command(budget=0))


async def test_소유_브랜드가_마감하면_CLOSED가_저장된다():
    repo = _StubCampaignRepository(_campaign())
    result = await CampaignPostingInteractor(repo).close(
        CloseCampaignCommand(campaign_id=1, actor_user_id=BRAND)
    )
    assert result.status == "CLOSED"
    assert repo.status_updates == [(1, CampaignStatus.CLOSED)]


async def test_남의_공고_마감은_NotCampaignOwnerError():
    interactor = CampaignPostingInteractor(_StubCampaignRepository(_campaign()))
    with pytest.raises(NotCampaignOwnerError):
        await interactor.close(CloseCampaignCommand(campaign_id=1, actor_user_id=999))


async def test_이미_마감된_공고면_InvalidCampaignStateError():
    interactor = CampaignPostingInteractor(
        _StubCampaignRepository(_campaign(status=CampaignStatus.CLOSED))
    )
    with pytest.raises(InvalidCampaignStateError):
        await interactor.close(CloseCampaignCommand(campaign_id=1, actor_user_id=BRAND))


async def test_없는_공고면_CampaignNotFoundError():
    interactor = CampaignPostingInteractor(_StubCampaignRepository())
    with pytest.raises(CampaignNotFoundError):
        await interactor.close(CloseCampaignCommand(campaign_id=9, actor_user_id=BRAND))
