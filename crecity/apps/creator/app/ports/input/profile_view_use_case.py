from __future__ import annotations

from abc import ABC, abstractmethod

from creator.app.dtos.profile_view_dto import ProfileViewRecordCommand, ProfileViewsResult


class ProfileViewUseCase(ABC):
    """프로필 조회수(갭 #57) — 공개 페이지에서 기록하고, 본인만 추이를 본다."""

    @abstractmethod
    async def record(self, command: ProfileViewRecordCommand) -> None:
        """조회 1건 기록 — 없는 슬러그는 조용히 무시한다(집계 기능이 404를 내지 않는다)."""
        ...

    @abstractmethod
    async def get_my_views(self, user_id: int) -> ProfileViewsResult: ...
