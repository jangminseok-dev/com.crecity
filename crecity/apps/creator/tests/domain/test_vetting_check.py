from creator.domain.entities.profile_analytics_entity import ProfileAnalytics
from creator.domain.value_objects.vetting_check import VettingCheck

MIN_FOLLOWERS, MIN_ENGAGEMENT = 1000, 10


def _analytics(platform: str, followers: int, engagement: int | None):
    return ProfileAnalytics(
        id=1,
        profile_id=1,
        platform=platform,
        followers_count=followers,
        engagement_permille=engagement,
        screenshot_file_name="shot.png",
    )


def _check(items):
    return VettingCheck.of(items, MIN_FOLLOWERS, MIN_ENGAGEMENT)


def test_기준을_모두_넘으면_통과():
    check = _check([_analytics("INSTAGRAM", 5000, 32)])
    assert (check.has_analytics, check.followers_ok, check.engagement_ok) == (True, True, True)
    assert check.passed is True


def test_팔로워는_전_채널_합산이다():
    check = _check([_analytics("INSTAGRAM", 700, 30), _analytics("YOUTUBE", 400, 5)])
    assert check.total_followers == 1100
    assert check.followers_ok is True


def test_참여율은_채널_중_최고값을_본다():
    check = _check([_analytics("INSTAGRAM", 2000, 4), _analytics("TIKTOK", 1500, 25)])
    assert check.best_engagement_permille == 25
    assert check.engagement_ok is True


def test_참여율_미입력이면_통과하지_못한다():
    check = _check([_analytics("INSTAGRAM", 9000, None)])
    assert check.best_engagement_permille is None
    assert (check.engagement_ok, check.passed) == (False, False)


def test_지표가_없으면_통과하지_못한다():
    check = _check([])
    assert (check.has_analytics, check.passed) == (False, False)


def test_팔로워가_기준_미만이면_통과하지_못한다():
    check = _check([_analytics("INSTAGRAM", 999, 50)])
    assert (check.followers_ok, check.passed) == (False, False)
