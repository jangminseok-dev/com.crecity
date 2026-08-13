import pytest

from order.domain.value_objects.ad_disclosure import has_ad_disclosure


@pytest.mark.parametrize(
    "caption",
    [
        "이 게시물은 광고입니다",
        "○○브랜드 협찬을 받아 촬영했어요",
        "#유료광고",
        "제품을 제공 받아 작성했습니다",
        "Paid partnership with ACME",
        "sponsored content",
        "새 향수 리뷰 #ad",
    ],
)
def test_대가성_표기가_있으면_통과(caption):
    assert has_ad_disclosure(caption) is True


@pytest.mark.parametrize(
    "caption",
    ["오늘 써본 립밤 후기예요", "advance 예약 오픈했어요", "", None],
)
def test_표기가_없으면_미확인(caption):
    assert has_ad_disclosure(caption) is False
