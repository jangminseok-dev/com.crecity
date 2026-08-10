from __future__ import annotations

from abc import ABC, abstractmethod

from creator.app.dtos.profile_listing_dto import ProfileListingQuery, ProfileListingResult


class ProfileListingUseCase(ABC):
    """마켓플레이스 공개 목록 유스케이스 — APPROVED 프로필만 노출한다.

    카테고리 목록 페이지(SSR)의 데이터 소스이며 프로그래매틱 SEO의 단위다
    (collabstr-analysis §7). PENDING·REJECTED는 목록에서 제외된다(§3.8).
    """

    @abstractmethod
    async def list_profiles(self, query: ProfileListingQuery) -> ProfileListingResult:
        """승인된 프로필을 최신 등록순으로 조회한다(카테고리·키워드 필터, 페이지네이션)."""
        ...

    @abstractmethod
    async def list_categories(self) -> list[str]:
        """승인 프로필의 카테고리 목록(중복 제거) — 홈 필터 칩 데이터."""
        ...
