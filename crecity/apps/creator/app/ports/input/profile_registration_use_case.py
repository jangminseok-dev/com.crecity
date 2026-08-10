from __future__ import annotations

from abc import ABC, abstractmethod

from creator.app.dtos.profile_registration_dto import (
    ProfileRegistrationCommand,
    ProfileRegistrationResult,
)


class ProfileRegistrationUseCase(ABC):
    """프로필 등록 유스케이스 — 등록 즉시 심사 대기(PENDING) 상태가 된다."""

    @abstractmethod
    async def register(self, command: ProfileRegistrationCommand) -> ProfileRegistrationResult:
        """슬러그 형식 검증·중복 확인 후 프로필을 생성한다.

        Raises:
            ValueError: 슬러그 형식 위반.
            DuplicateSlugError: 이미 사용 중인 슬러그.
        """
        ...
