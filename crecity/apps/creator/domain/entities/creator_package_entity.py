from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class PackagePlatform(StrEnum):
    """패키지가 납품되는 채널 — 네이버 블로그는 국내 협찬 시장 필수 채널(현지화 §9.2).

    UGC는 플랫폼 게시 없이 콘텐츠만 납품하는 유형(팔로워 0이어도 판매 가능 — collabstr §2.2).
    """

    INSTAGRAM = "INSTAGRAM"
    YOUTUBE = "YOUTUBE"
    TIKTOK = "TIKTOK"
    NAVER_BLOG = "NAVER_BLOG"
    UGC = "UGC"


@dataclass(frozen=True, slots=True)
class CreatorPackage:
    """가격 공개 판매 패키지 — 프로필 페이지의 핵심 전환 단위(collabstr §2.1)."""

    id: int
    profile_id: int
    platform: PackagePlatform
    title: str  # 예: "인스타그램 릴스 1개"
    description: str  # 납품물·수정 횟수 등 상세
    price_krw: int
    created_at: datetime | None = None
