from datetime import datetime, timedelta, timezone

import pytest

from campaign.domain.entities.campaign_entity import (
    Campaign,
    CampaignPlatform,
    CampaignStatus,
    InvalidCampaignStateError,
    NotCampaignOwnerError,
)

_NOW = datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)
BRAND, OTHER = 100, 999


def _campaign(status=CampaignStatus.OPEN, deadline_at=None):
    return Campaign(
        id=1, brand_user_id=BRAND, title="신제품 릴스 캠페인", description="설명",
        platform=CampaignPlatform.INSTAGRAM, budget_krw=500000,
        status=status, deadline_at=deadline_at,
    )


# ── 마감(수동) ─────────────────────────────────────────────────────────────


def test_소유_브랜드만_마감할_수_있다():
    assert _campaign().close(BRAND).status is CampaignStatus.CLOSED
    with pytest.raises(NotCampaignOwnerError):
        _campaign().close(OTHER)


def test_이미_마감된_공고는_재마감할_수_없다():
    with pytest.raises(InvalidCampaignStateError):
        _campaign(CampaignStatus.CLOSED).close(BRAND)


# ── 지원 가능 여부 (마감일 포함, 갭 #27) ──────────────────────────────────


def test_마감일_전이면_지원할_수_있다():
    _campaign(deadline_at=_NOW + timedelta(hours=1)).ensure_open_for_application(_NOW)


def test_마감일이_지나면_스윕_전이라도_지원이_막힌다():
    with pytest.raises(InvalidCampaignStateError):
        _campaign(deadline_at=_NOW - timedelta(minutes=1)).ensure_open_for_application(_NOW)


def test_마감일이_없으면_상태만_본다():
    _campaign().ensure_open_for_application(_NOW)
    with pytest.raises(InvalidCampaignStateError):
        _campaign(CampaignStatus.CLOSED).ensure_open_for_application(_NOW)


# ── 만료(주기 스캔) ────────────────────────────────────────────────────────


def test_마감일_경과_공고는_expire로_마감된다():
    expired = _campaign(deadline_at=_NOW - timedelta(minutes=1)).expire(_NOW)
    assert expired is not None and expired.status is CampaignStatus.CLOSED


def test_마감일_전이거나_없으면_expire_대상이_아니다():
    assert _campaign(deadline_at=_NOW + timedelta(hours=1)).expire(_NOW) is None
    assert _campaign().expire(_NOW) is None


def test_이미_마감된_공고는_expire_대상이_아니다():
    assert (
        _campaign(CampaignStatus.CLOSED, deadline_at=_NOW - timedelta(hours=1)).expire(_NOW)
        is None
    )
