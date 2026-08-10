from __future__ import annotations

from abc import ABC, abstractmethod

from creator.app.dtos.my_profile_lookup_dto import MyProfileQuery, MyProfileResult


class MyProfileLookupUseCase(ABC):
    """내 프로필 조회 유스케이스 — 대시보드가 로그인 사용자의 프로필을 확인한다."""

    @abstractmethod
    async def get_my_profile(self, query: MyProfileQuery) -> MyProfileResult:
        """로그인 사용자의 프로필을 조회한다.

        Raises:
            ProfileNotFoundError: 아직 등록한 프로필 없음.
        """
        ...
