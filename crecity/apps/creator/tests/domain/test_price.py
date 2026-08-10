import pytest

from creator.domain.value_objects.price import Price


@pytest.mark.parametrize("krw", [1, 175000, 10_000_000])
def test_양수_가격은_통과한다(krw):
    assert Price(krw).krw == krw


@pytest.mark.parametrize("krw", [0, -1, -175000])
def test_0이하_가격은_ValueError(krw):
    with pytest.raises(ValueError):
        Price(krw)
