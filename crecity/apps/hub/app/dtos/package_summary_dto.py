from dataclasses import dataclass


@dataclass(frozen=True)
class PackageSummary:
    """주문 생성 검증용 패키지 요약 — order → creator 허브 계약(BOUNDARIES §5).

    creator_user_id는 구매 확정 시 적립 대상(패키지 소유 프로필의 계정)이다.
    """

    package_id: int
    title: str
    price_krw: int
    creator_user_id: int
