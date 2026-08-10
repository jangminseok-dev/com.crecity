from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum


class CampaignPlatform(StrEnum):
    """공고 타깃 플랫폼 — 스포크 독립 원칙상 campaign이 자체 정의한다(creator enum 미참조)."""

    INSTAGRAM = "INSTAGRAM"
    YOUTUBE = "YOUTUBE"
    TIKTOK = "TIKTOK"
    NAVER_BLOG = "NAVER_BLOG"
    UGC = "UGC"


class CampaignStatus(StrEnum):
    OPEN = "OPEN"  # 지원 접수 중
    CLOSED = "CLOSED"  # 브랜드가 마감


class InvalidCampaignStateError(Exception):
    """공고 상태 위반(마감 공고 지원·재마감 등) — 라우터에서 409로 변환."""


class NotCampaignOwnerError(Exception):
    """공고를 올린 브랜드가 아님 — 라우터에서 403으로 변환."""


@dataclass(frozen=True, slots=True)
class Campaign:
    """역경매 공고 — 브랜드가 올리고 크리에이터가 견적으로 지원한다(collabstr 캠페인)."""

    id: int
    brand_user_id: int
    title: str
    description: str  # 원하는 콘텐츠·조건
    platform: CampaignPlatform
    budget_krw: int  # 예산 상한(참고 정보 — 지원 견적은 자유)
    status: CampaignStatus
    created_at: datetime | None = None

    def close(self, actor_user_id: int) -> Campaign:
        """브랜드 마감 — 이후 지원 불가."""
        if actor_user_id != self.brand_user_id:
            raise NotCampaignOwnerError("공고를 올린 브랜드만 마감할 수 있습니다.")
        if self.status is not CampaignStatus.OPEN:
            raise InvalidCampaignStateError("이미 마감된 공고입니다.")
        return replace(self, status=CampaignStatus.CLOSED)

    def ensure_open_for_application(self) -> None:
        if self.status is not CampaignStatus.OPEN:
            raise InvalidCampaignStateError("마감된 공고에는 지원할 수 없습니다.")


@dataclass(frozen=True, slots=True)
class CampaignApplication:
    """공고 지원 — 크리에이터의 자체 견적 제안. 공고당 크리에이터 1회."""

    id: int
    campaign_id: int
    creator_user_id: int
    message: str  # 제안 내용
    proposed_price_krw: int
    created_at: datetime | None = None
