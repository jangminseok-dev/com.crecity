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
    deadline_at: datetime | None = None  # 지원 마감일(선택) — 경과 시 주기 스캔이 자동 마감
    target_category: str | None = None  # 타겟 니치(선택, §3.2)
    target_location: str | None = None  # 타겟 활동 지역(선택, §3.2)
    created_at: datetime | None = None

    def close(self, actor_user_id: int) -> Campaign:
        """브랜드 마감 — 이후 지원 불가."""
        if actor_user_id != self.brand_user_id:
            raise NotCampaignOwnerError("공고를 올린 브랜드만 마감할 수 있습니다.")
        if self.status is not CampaignStatus.OPEN:
            raise InvalidCampaignStateError("이미 마감된 공고입니다.")
        return replace(self, status=CampaignStatus.CLOSED)

    def ensure_open_for_application(self, now: datetime) -> None:
        """지원 가능 여부 — 상태와 마감일 둘 다 본다(스윕 주기와 무관하게 마감일이 정본)."""
        if self.status is not CampaignStatus.OPEN:
            raise InvalidCampaignStateError("마감된 공고에는 지원할 수 없습니다.")
        if self.deadline_at is not None and now >= self.deadline_at:
            raise InvalidCampaignStateError("지원 마감일이 지난 공고입니다.")

    def expire(self, now: datetime) -> Campaign | None:
        """마감일 경과 → 자동 마감(주기 스캔 전용). 대상이 아니면 None."""
        if self.status is not CampaignStatus.OPEN:
            return None
        if self.deadline_at is None or now < self.deadline_at:
            return None
        return replace(self, status=CampaignStatus.CLOSED)


@dataclass(frozen=True, slots=True)
class CampaignApplication:
    """공고 지원 — 크리에이터의 자체 견적 제안. 공고당 크리에이터 1회."""

    id: int
    campaign_id: int
    creator_user_id: int
    message: str  # 제안 내용
    proposed_price_krw: int
    order_id: int | None = None  # 수락(결제) 시 생성된 주문 — 논리 참조, 재결제 차단 표식
    created_at: datetime | None = None

    def is_payable(self) -> bool:
        """아직 주문으로 이어지지 않은 지원만 수락(결제) 가능하다."""
        return self.order_id is None
