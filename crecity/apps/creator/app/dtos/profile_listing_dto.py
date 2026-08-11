from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ProfileListingQuery:

    category: str | None
    q: str | None  # 키워드 — 이름·한 줄 소개 부분 일치
    limit: int
    offset: int


@dataclass(frozen=True)
class ProfileListingItem:

    id: int
    slug: str
    name: str
    tagline: str
    location: str | None
    primary_category: str
    created_at: datetime | None
    # 카드 보강 필드 — 없으면 None/0 (2026-08-11)
    cover_file_name: str | None = None  # 첫 포트폴리오 사진 — URL 변환은 라우터 몫
    price_from: int | None = None  # 최저 패키지 가격
    rating_avg: float | None = None  # 3축 평균의 평균(리뷰 앱 집계 의미와 동일)
    rating_count: int = 0


@dataclass(frozen=True)
class ProfileListingResult:

    items: list[ProfileListingItem]
    total: int
