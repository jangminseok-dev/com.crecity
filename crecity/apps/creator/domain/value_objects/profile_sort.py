from enum import StrEnum


class ProfileSort(StrEnum):
    """마켓플레이스 목록 정렬 기준(§3.1, 갭 #45).

    가격은 프로필의 **최저 패키지 가격** 기준이며, 패키지가 없는 프로필은 항상 뒤로 보낸다.
    평점·인기순은 다른 스포크(review·order)가 소유한 데이터라 DB 정렬을 할 수 없다 —
    인기순은 별도 엔드포인트(`GET /creator/profiles/popular`)가 담당한다.
    """

    LATEST = "latest"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
