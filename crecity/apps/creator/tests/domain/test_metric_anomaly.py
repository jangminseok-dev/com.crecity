from creator.domain.value_objects.metric_anomaly import detect_anomaly

_BASE = dict(surge_multiplier=3, engagement_floor_followers=10000, max_engagement_permille=150)


def test_정상_지표는_플래그가_없다():
    assert detect_anomaly(10000, 12000, 35, **_BASE) is None


def test_첫_제출은_급증_비교_대상이_없다():
    assert detect_anomaly(None, 1_000_000, 35, **_BASE) is None


def test_재제출_급증은_플래그된다():
    reason = detect_anomaly(10000, 30000, 35, **_BASE)
    assert reason is not None and "급증" in reason


def test_대형_계정_고참여율은_플래그된다():
    reason = detect_anomaly(None, 50000, 200, **_BASE)
    assert reason is not None and "고참여율" in reason


def test_소형_계정_고참여율은_정상이다():
    # 마이크로 계정은 참여율이 높은 게 자연스럽다 — floor 미만은 판정하지 않는다
    assert detect_anomaly(None, 900, 300, **_BASE) is None
