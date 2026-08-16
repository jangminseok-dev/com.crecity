import pytest

from campaign.app.dtos.campaign_application_dto import ApplicationsQuery, ApplyCommand
from campaign.app.exceptions import (
    AlreadyAppliedError,
    CampaignNotFoundError,
    CreatorProfileRequiredError,
    NotCreatorAccountError,
)
from campaign.app.use_cases.campaign_application_interactor import CampaignApplicationInteractor
from campaign.domain.entities.campaign_entity import (
    Campaign,
    CampaignApplication,
    CampaignPlatform,
    CampaignStatus,
    InvalidCampaignStateError,
    NotCampaignOwnerError,
)
from hub.app.dtos.creator_ref_dto import CreatorRef

BRAND, CREATOR = 100, 200
_REF = CreatorRef(creator_user_id=CREATOR, slug="kim-beauty", name="김뷰티")


class _StubCampaignRepository:
    def __init__(self, campaign: Campaign | None):
        self.campaign = campaign

    async def create(self, **kwargs):
        raise NotImplementedError

    async def find_by_id(self, campaign_id):
        return self.campaign if self.campaign and self.campaign.id == campaign_id else None

    async def update_status(self, campaign_id, status):
        raise NotImplementedError

    async def list_by_status(self, status, limit, offset):
        raise NotImplementedError

    async def list_by_brand(self, brand_user_id):
        raise NotImplementedError


class _StubApplicationRepository:
    def __init__(self, existing: list[CampaignApplication] | None = None):
        self.applications = list(existing or [])
        self.published: list = []          # 함께 적재된 알림 이벤트(갭 #73)

    async def create(self, campaign_id, creator_user_id, message, proposed_price_krw, events=None):
        self.published += list(events or [])
        application = CampaignApplication(
            id=len(self.applications) + 1, campaign_id=campaign_id,
            creator_user_id=creator_user_id, message=message,
            proposed_price_krw=proposed_price_krw,
        )
        self.applications.append(application)
        return application

    async def exists(self, campaign_id, creator_user_id):
        return any(
            a.campaign_id == campaign_id and a.creator_user_id == creator_user_id
            for a in self.applications
        )

    async def list_by_campaign(self, campaign_id, sort=None, only_open=False):
        return [a for a in self.applications if a.campaign_id == campaign_id]


class _StubCreatorRefPort:
    def __init__(self, ref: CreatorRef | None = _REF):
        self.ref = ref

    async def get_creator_by_slug(self, slug):
        raise NotImplementedError

    async def get_creator_by_user_id(self, user_id):
        return self.ref if self.ref and self.ref.creator_user_id == user_id else None


def _campaign(status=CampaignStatus.OPEN):
    return Campaign(
        id=1, brand_user_id=BRAND, title="신제품 릴스", description="설명",
        platform=CampaignPlatform.INSTAGRAM, budget_krw=500000, status=status,
    )


def _interactor(campaign=None, applications=None, ref=_REF):
    return CampaignApplicationInteractor(
        campaigns=_StubCampaignRepository(campaign if campaign is not None else _campaign()),
        applications=applications if applications is not None else _StubApplicationRepository(),
        creators=_StubCreatorRefPort(ref),
    )


def _apply_command(account_type="CREATOR", price=400000):
    return ApplyCommand(
        campaign_id=1, creator_user_id=CREATOR, account_type=account_type,
        message="이런 방향으로 제작해 드릴 수 있습니다.", proposed_price_krw=price,
    )


async def test_크리에이터가_견적으로_지원한다():
    result = await _interactor().apply(_apply_command())
    assert result.creator_name == "김뷰티"  # 허브로 실시간 해석
    assert result.creator_slug == "kim-beauty"
    assert result.proposed_price_krw == 400000


async def test_마감된_공고면_InvalidCampaignStateError():
    with pytest.raises(InvalidCampaignStateError):
        await _interactor(campaign=_campaign(status=CampaignStatus.CLOSED)).apply(_apply_command())


async def test_중복_지원이면_AlreadyAppliedError():
    applications = _StubApplicationRepository()
    interactor = _interactor(applications=applications)
    await interactor.apply(_apply_command())
    with pytest.raises(AlreadyAppliedError):
        await interactor.apply(_apply_command())


async def test_프로필_없는_크리에이터면_CreatorProfileRequiredError():
    with pytest.raises(CreatorProfileRequiredError):
        await _interactor(ref=None).apply(_apply_command())


async def test_브랜드_계정_지원은_NotCreatorAccountError():
    with pytest.raises(NotCreatorAccountError):
        await _interactor().apply(_apply_command(account_type="BRAND"))


async def test_지원자_목록은_공고_브랜드만_본다():
    applications = _StubApplicationRepository()
    interactor = _interactor(applications=applications)
    await interactor.apply(_apply_command())

    results = await interactor.list_applications(
        ApplicationsQuery(campaign_id=1, requester_user_id=BRAND)
    )
    assert len(results) == 1
    with pytest.raises(NotCampaignOwnerError):
        await interactor.list_applications(
            ApplicationsQuery(campaign_id=1, requester_user_id=999)
        )


async def test_없는_공고_지원이면_CampaignNotFoundError():
    interactor = CampaignApplicationInteractor(
        campaigns=_StubCampaignRepository(None),
        applications=_StubApplicationRepository(),
        creators=_StubCreatorRefPort(),
    )
    with pytest.raises(CampaignNotFoundError):
        await interactor.apply(_apply_command())


async def test_지원하면_공고를_올린_브랜드에게_알림이_간다():
    """지원 사실을 모르면 공고를 올린 의미가 없다(갭 #73)."""
    applications = _StubApplicationRepository()
    interactor = CampaignApplicationInteractor(
        _StubCampaignRepository(_campaign()), applications, _StubCreatorRefPort()
    )
    await interactor.apply(
        ApplyCommand(
            campaign_id=1, creator_user_id=CREATOR, account_type="CREATOR",
            message="지원합니다", proposed_price_krw=300_000,
        )
    )
    assert len(applications.published) == 1
    event = applications.published[0]
    assert event.event_type == "campaign.application_received"
    assert event.payload["brand_user_id"] == BRAND
