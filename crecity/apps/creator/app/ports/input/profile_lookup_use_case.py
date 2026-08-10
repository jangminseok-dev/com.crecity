from __future__ import annotations

from abc import ABC, abstractmethod

from creator.app.dtos.profile_lookup_dto import ProfileLookupQuery, ProfileLookupResult


class ProfileLookupUseCase(ABC):
    """슬러그 공개 조회 유스케이스 — 프로필 페이지(SSR)의 데이터 소스.

    REJECTED 프로필도 직접 링크로는 조회된다(마켓 목록 제외만 — collabstr §3.8).
    """

    @abstractmethod
    async def lookup(self, query: ProfileLookupQuery) -> ProfileLookupResult:
        """슬러그로 프로필을 조회한다.

        Raises:
            ProfileNotFoundError: 해당 슬러그의 프로필 없음.
        """
        ...
