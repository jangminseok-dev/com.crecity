from dataclasses import dataclass


@dataclass(frozen=True)
class CustomOfferSummary:
    """결제 가능한 커스텀 오퍼 요약 — chat이 채워 준다."""

    offer_id: int
    title: str
    price_krw: int
    brand_user_id: int  # 이 브랜드만 결제 가능
    creator_user_id: int  # 주문 적립 대상
    # 합의 조건(갭 #98) — 주문 계약 조건 스냅샷 재료
    revision_limit: int = 2
    usage_rights: str = ""
