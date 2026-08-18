from creator.domain.value_objects.trust_check import is_trusted_creator

_BASE = dict(min_verified_channels=1, min_completed_orders=3)


def test_기준_충족이면_신뢰_크리에이터():
    assert is_trusted_creator(1, 3, 0, 0, **_BASE)


def test_인증_채널_부족이면_아니다():
    assert not is_trusted_creator(0, 10, 0, 0, **_BASE)


def test_완료_거래_부족이면_아니다():
    assert not is_trusted_creator(2, 2, 0, 0, **_BASE)


def test_무응답_만료가_있으면_아니다():
    assert not is_trusted_creator(2, 10, 1, 0, **_BASE)


def test_분쟁_패소가_있으면_아니다():
    assert not is_trusted_creator(2, 10, 0, 1, **_BASE)
