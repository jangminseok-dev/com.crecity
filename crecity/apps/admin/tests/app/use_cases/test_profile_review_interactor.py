from datetime import datetime, timezone

import pytest

from admin.app.dtos.profile_review_dto import ReviewDecisionCommand
from admin.app.exceptions import ReviewTargetNotFoundError
from admin.app.use_cases.profile_review_interactor import ProfileReviewInteractor
from hub.app.dtos.profile_review_dto import ProfileReviewSummary

_NOW = datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc)


def _summary(id=1, status="PENDING"):
    return ProfileReviewSummary(
        id=id,
        slug="kim-beauty",
        name="김뷰티",
        tagline="스킨케어 리뷰",
        bio="소개",
        primary_category="뷰티",
        status=status,
        created_at=_NOW,
    )


class _StubProfileReviewPort:
    def __init__(self, pending: list[ProfileReviewSummary] | None = None):
        self.pending = pending or []
        self.reviewed = []  # (profile_id, approved)

    async def list_pending_profiles(self):
        return self.pending

    async def review_profile(self, profile_id, approved, reason=None):
        self.reviewed.append((profile_id, approved, reason))
        if not any(p.id == profile_id for p in self.pending):
            return None
        return _summary(id=profile_id, status="APPROVED" if approved else "REJECTED")


class _StubRecord:
    def __init__(self):
        self.records = []

    async def record(self, subject, note):
        self.records.append((subject, note))


def _command(profile_id=1, approved=True, reason=None):
    return ReviewDecisionCommand(
        profile_id=profile_id, approved=approved, reviewer_id=2,
        reviewer_email="admin@crecity.com", reason=reason,
    )


async def test_심사_대기_목록을_허브_계약으로_가져온다():
    interactor = ProfileReviewInteractor(_StubProfileReviewPort([_summary()]), _StubRecord())
    results = await interactor.list_pending()
    assert len(results) == 1
    assert results[0].status == "PENDING"


async def test_승인하면_전이되고_감사_기록이_남는다():
    port, record = _StubProfileReviewPort([_summary()]), _StubRecord()
    result = await ProfileReviewInteractor(port, record).review(_command(approved=True))
    assert result.status == "APPROVED"
    assert port.reviewed == [(1, True, None)]
    assert "승인" in record.records[0][1]
    assert "admin@crecity.com" in record.records[0][1]  # 누가 심사했는지 남는다


async def test_반려_사유가_포트와_감사_기록에_실린다():
    port, record = _StubProfileReviewPort([_summary()]), _StubRecord()
    await ProfileReviewInteractor(port, record).review(
        _command(approved=False, reason="포트폴리오가 비어 있습니다")
    )
    assert port.reviewed == [(1, False, "포트폴리오가 비어 있습니다")]
    assert "반려(사유: 포트폴리오가 비어 있습니다)" in record.records[0][1]


async def test_반려하면_REJECTED로_전이된다():
    port = _StubProfileReviewPort([_summary()])
    result = await ProfileReviewInteractor(port, _StubRecord()).review(_command(approved=False))
    assert result.status == "REJECTED"


async def test_대상이_없으면_ReviewTargetNotFoundError_기록_없음():
    record = _StubRecord()
    interactor = ProfileReviewInteractor(_StubProfileReviewPort([]), record)
    with pytest.raises(ReviewTargetNotFoundError):
        await interactor.review(_command(profile_id=99))
    assert record.records == []
