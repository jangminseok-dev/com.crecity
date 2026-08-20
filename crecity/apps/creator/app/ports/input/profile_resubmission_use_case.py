from __future__ import annotations

from abc import ABC, abstractmethod

from creator.app.dtos.my_profile_lookup_dto import MyProfileResult
from creator.app.dtos.profile_resubmission_dto import ProfileResubmissionCommand


class ProfileResubmissionUseCase(ABC):
    """반려 프로필 재심사 요청(갭 #101) — REJECTED → PENDING 복귀."""

    @abstractmethod
    async def resubmit(self, command: ProfileResubmissionCommand) -> MyProfileResult: ...
