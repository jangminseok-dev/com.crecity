from dataclasses import dataclass


@dataclass(frozen=True)
class CampaignApplicationSummary:
    """결제(수락) 가능한 캠페인 지원 요약 — campaign이 채워 준다."""

    application_id: int
    campaign_id: int
    title: str  # 공고 제목 — 결제창·주문 제목으로 쓴다
    price_krw: int  # 크리에이터 제안 견적
    brand_user_id: int  # 공고 소유 브랜드만 결제 가능
    creator_user_id: int  # 주문 적립 대상(지원 크리에이터)
