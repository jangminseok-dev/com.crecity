import pytest

from review.domain.entities.review_entity import InvalidScoreError, Review, validate_score


def _review(communication=5, timeliness=4, satisfaction=3):
    return Review(
        id=1, order_id=10, brand_user_id=100, creator_user_id=200,
        communication_score=communication, timeliness_score=timeliness,
        satisfaction_score=satisfaction, comment="좋았습니다",
    )


def test_종합_평점은_3축_평균_소수_1자리():
    assert _review(5, 4, 3).overall_score() == 4.0
    assert _review(5, 5, 4).overall_score() == 4.7


def test_평점_범위를_벗어나면_InvalidScoreError():
    with pytest.raises(InvalidScoreError):
        validate_score("소통", 0)
    with pytest.raises(InvalidScoreError):
        validate_score("만족도", 6)
    assert validate_score("기한", 3) == 3
