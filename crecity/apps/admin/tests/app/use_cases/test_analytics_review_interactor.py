import pytest

from admin.app.dtos.analytics_review_dto import ClearFlagCommand
from admin.app.exceptions import ReviewTargetNotFoundError
from admin.app.use_cases.analytics_review_interactor import AnalyticsReviewInteractor
from hub.app.dtos.profile_review_dto import FlaggedAnalyticsSummary


class _StubReviewPort:
    def __init__(self, flagged=(), clear_ok=True):
        self.flagged = list(flagged)
        self.clear_ok = clear_ok
        self.cleared = []

    async def list_flagged_analytics(self):
        return self.flagged

    async def clear_analytics_flag(self, analytics_id):
        self.cleared.append(analytics_id)
        return self.clear_ok


class _StubRecord:
    def __init__(self):
        self.notes = []

    async def record(self, subject, note):
        self.notes.append((subject, note))


_ROW = FlaggedAnalyticsSummary(
    id=5, profile_slug="kim-beauty", profile_name="김뷰티", platform="INSTAGRAM",
    followers_count=999000, engagement_permille=250,
    flag_reason="팔로워 급증: 12,000 → 999,000", updated_at=None,
)


async def test_플래그_목록을_그대로_내려준다():
    interactor = AnalyticsReviewInteractor(_StubReviewPort([_ROW]), _StubRecord())
    result = await interactor.list_flagged()
    assert result[0].flag_reason.startswith("팔로워 급증")


async def test_확인_처리하면_해제와_감사_기록이_남는다():
    port, record = _StubReviewPort([_ROW]), _StubRecord()
    await AnalyticsReviewInteractor(port, record).clear_flag(
        ClearFlagCommand(analytics_id=5, reviewer_id=1, reviewer_email="admin@crecity.kr")
    )
    assert port.cleared == [5]
    assert record.notes[0][0] == "analytics_review"


async def test_대상이_없으면_ReviewTargetNotFoundError():
    interactor = AnalyticsReviewInteractor(_StubReviewPort(clear_ok=False), _StubRecord())
    with pytest.raises(ReviewTargetNotFoundError):
        await interactor.clear_flag(
            ClearFlagCommand(analytics_id=9, reviewer_id=1, reviewer_email="admin@crecity.kr")
        )
