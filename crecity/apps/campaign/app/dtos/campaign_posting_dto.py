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
    deadline_at: datetime | None = None  # 지원 마감일(선택) — 경과 시 자동 마감
    target_category: str | None = None  # 타겟 니치(선택, §3.2)
    target_location: str | None = None  # 타겟 지역(선택, §3.2)


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
    deadline_at: datetime | None
    target_category: str | None
    target_location: str | None
    created_at: datetime | None
