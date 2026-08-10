from __future__ import annotations

from abc import ABC, abstractmethod

from creator.app.dtos.my_profile_lookup_dto import MyProfileResult
from creator.app.dtos.profile_update_dto import ProfileUpdateCommand


class ProfileUpdateUseCase(ABC):
    """내 프로필 수정 유스케이스 — 심사 상태는 유지된다(승인 후 자유 수정, collabstr §3.8)."""

    @abstractmethod
    async def update_my_profile(self, command: ProfileUpdateCommand) -> MyProfileResult:
        """로그인 사용자의 프로필을 수정한다.

        Raises:
            ProfileNotFoundError: 등록한 프로필 없음.
        """
        ...
