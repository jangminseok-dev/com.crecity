from order.domain.value_objects.response_speed import avg_accept_hours, is_fast_responder

_HOUR = 3600.0


def test_평균_수락_시간은_소수_1자리_시간으로_변환된다():
    assert avg_accept_hours(None) is None
    assert avg_accept_hours(1800.0) == 0.5
    assert avg_accept_hours(5 * _HOUR + 400) == 5.1


def test_기준을_모두_충족하면_빠른_응답이다():
    assert is_fast_responder(
        6 * _HOUR, responded_exits=3, expired_exits=0, threshold_hours=24, min_samples=3
    )


def test_표본이_모자라면_배지가_없다():
    assert not is_fast_responder(
        1 * _HOUR, responded_exits=2, expired_exits=0, threshold_hours=24, min_samples=3
    )


def test_무응답_만료가_있으면_배지가_없다():
    # 빨리 수락할 주문만 골라 받고 나머지를 방치하는 계정을 걸러낸다
    assert not is_fast_responder(
        1 * _HOUR, responded_exits=5, expired_exits=1, threshold_hours=24, min_samples=3
    )


def test_평균이_임계를_넘으면_배지가_없다():
    assert not is_fast_responder(
        25 * _HOUR, responded_exits=5, expired_exits=0, threshold_hours=24, min_samples=3
    )


def test_수락_이력이_없으면_배지가_없다():
    assert not is_fast_responder(
        None, responded_exits=0, expired_exits=0, threshold_hours=24, min_samples=3
    )


def test_거절만으로는_배지가_없다():
    # 거절 표본만으로 min_samples를 채우면 avg가 None이라 배지 없음 — 수락 실적이 있어야 한다
    assert not is_fast_responder(
        None, responded_exits=3, expired_exits=0, threshold_hours=24, min_samples=3
    )
