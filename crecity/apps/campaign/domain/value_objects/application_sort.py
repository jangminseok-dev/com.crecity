from enum import StrEnum


class ApplicationSort(StrEnum):
    """지원자 정렬(갭 #70).

    캠페인이 소유한 값(지원 시각·제시 견적)으로만 정렬한다 — 평점·팔로워는 다른 스포크
    소유라 DB 정렬이 스포크 경계를 넘는다(갭 #45와 같은 이유).
    """

    OLDEST = "oldest"  # 먼저 지원한 순(기본)
    LATEST = "latest"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
