from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PostCampaignCommand:

    title: str
    description: str
    platform: str
    budget_krw: int
    brand_user_id: int  # 로그인 사용자 (허브 계약으로 검증됨)
    account_type: str  # BRAND만


@dataclass(frozen=True)
class CloseCampaignCommand:

    campaign_id: int
    actor_user_id: int


@dataclass(frozen=True)
class CampaignResult:
    """공고 응답 DTO — posting·listing 슬라이스가 공유한다(도메인어 명명 예외)."""

    id: int
    brand_user_id: int
    title: str
    description: str
    platform: str
    budget_krw: int
    status: str
    created_at: datetime | None
