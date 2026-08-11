from __future__ import annotations

from abc import ABC, abstractmethod

from creator.app.dtos.analytics_management_dto import (
    AnalyticsResult,
    RemoveAnalyticsCommand,
    SubmitAnalyticsCommand,
)


class AnalyticsManagementUseCase(ABC):
    """채널 분석 지표(팔로워·참여율) 자가입력 유스케이스 — §9.2, 갭 #14.

    공개 열람은 로그인 필수(가입 게이트) — 게이트 자체는 라우터 DI(get_current_user)가 담당.
    """

    @abstractmethod
    async def submit(self, command: SubmitAnalyticsCommand) -> AnalyticsResult:
        """플랫폼별 지표 제출(재제출 시 갱신).

        Raises:
            ProfileNotFoundError: 내 프로필 없음.
            ValueError: 플랫폼·수치·스크린샷 형식 위반.
        """
        ...

    @abstractmethod
    async def list_mine(self, requester_user_id: int) -> list[AnalyticsResult]:
        """내 지표 목록 — 대시보드 관리용.

        Raises:
            ProfileNotFoundError: 내 프로필 없음.
        """
        ...

    @abstractmethod
    async def remove(self, command: RemoveAnalyticsCommand) -> None:
        """플랫폼 지표 삭제.

        Raises:
            ProfileNotFoundError: 내 프로필 없음.
            AnalyticsNotFoundError: 해당 플랫폼 지표 없음.
        """
        ...

    @abstractmethod
    async def list_public(self, slug: str) -> list[AnalyticsResult]:
        """프로필의 지표 목록(Analytics 섹션) — 로그인 사용자에게만 라우터가 연다.

        Raises:
            ProfileNotFoundError: 프로필 없음.
        """
        ...
