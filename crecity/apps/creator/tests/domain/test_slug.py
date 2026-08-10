import pytest

from creator.domain.value_objects.slug import Slug


@pytest.mark.parametrize("value", ["kim-beauty", "abc", "a1-b2-c3", "0" * 30])
def test_유효한_슬러그는_통과한다(value):
    assert Slug(value).value == value


@pytest.mark.parametrize(
    "value",
    [
        "ab",  # 3자 미만
        "a" * 31,  # 30자 초과
        "Kim-Beauty",  # 대문자
        "김뷰티",  # 한글
        "-kim",  # 하이픈 시작
        "kim-",  # 하이픈 끝
        "kim beauty",  # 공백
        "kim_beauty",  # 언더스코어
        "",
    ],
)
def test_형식_위반_슬러그는_ValueError(value):
    with pytest.raises(ValueError):
        Slug(value)
