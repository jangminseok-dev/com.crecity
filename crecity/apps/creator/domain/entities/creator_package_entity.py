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


# 수정 횟수 기본값 — 표준계약 조항의 관행치(§9.2). 0이면 수정 불가 상품
DEFAULT_REVISION_LIMIT = 2


@dataclass(frozen=True, slots=True)
class CreatorPackage:
    """가격 공개 판매 패키지 — 프로필 페이지의 핵심 전환 단위(collabstr §2.1)."""

    id: int
    profile_id: int
    platform: PackagePlatform
    title: str  # 예: "인스타그램 릴스 1개"
    description: str  # 납품물 등 상세
    price_krw: int
    # 표준계약 조항의 구조화 필드(§3.3·§9.2, 갭 #29) — 주문 생성 시 스냅샷된다
    revision_limit: int = DEFAULT_REVISION_LIMIT  # 브랜드가 요청할 수 있는 수정 횟수
    usage_rights: str = ""  # 2차 활용 범위(예: "SNS 게시 6개월, 유료 광고 별도 협의")
    created_at: datetime | None = None
