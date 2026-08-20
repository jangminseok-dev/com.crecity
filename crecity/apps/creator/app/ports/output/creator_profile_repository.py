from __future__ import annotations

from abc import ABC, abstractmethod

from creator.domain.entities.creator_profile_entity import CreatorProfile, ProfileStatus
from creator.domain.value_objects.profile_sort import ProfileSort


class CreatorProfileRepository(ABC):
    """프로필 영속성 포트 — 등록·조회 슬라이스가 공유한다(도메인어 명명 예외)."""

    @abstractmethod
    async def create(
        self,
        slug: str,
        name: str,
        tagline: str,
        bio: str,
        location: str | None,
        primary_category: str,
        status: ProfileStatus,
        user_id: int,
    ) -> CreatorProfile: ...

    @abstractmethod
    async def find_by_id(self, profile_id: int) -> CreatorProfile | None: ...

    @abstractmethod
    async def find_by_slug(self, slug: str) -> CreatorProfile | None: ...

    @abstractmethod
    async def find_by_user_id(self, user_id: int) -> CreatorProfile | None:
        """소유 계정으로 조회 — 1인 1프로필 검증에 쓴다."""
        ...

    @abstractmethod
    async def exists_by_slug(self, slug: str) -> bool: ...

    @abstractmethod
    async def list_by_status(
        self,
        status: ProfileStatus,
        category: str | None,
        limit: int,
        offset: int,
        q: str | None = None,
        platform: str | None = None,
        price_min: int | None = None,
        price_max: int | None = None,
        location: str | None = None,
        sort: ProfileSort = ProfileSort.LATEST,
        followers_min: int | None = None,
        engagement_min: int | None = None,
    ) -> list[CreatorProfile]:
        """상태로 필터한 프로필을 sort 기준으로 조회한다(§3.1 검색 필터·정렬).

        q는 이름·한 줄 소개 부분 일치, location은 부분 일치.
        platform·price_min/max는 "해당 조건의 패키지가 하나라도 있는 프로필"(EXISTS).
        """
        ...

    @abstractmethod
    async def count_by_status(
        self,
        status: ProfileStatus,
        category: str | None,
        q: str | None = None,
        platform: str | None = None,
        price_min: int | None = None,
        price_max: int | None = None,
        location: str | None = None,
        followers_min: int | None = None,
        engagement_min: int | None = None,
    ) -> int: ...

    @abstractmethod
    async def list_by_user_ids(
        self, user_ids: list[int], status: ProfileStatus
    ) -> list[CreatorProfile]:
        """소유 계정 id들로 조회(상태 필터) — 인기 순위를 프로필로 해석할 때 쓴다."""
        ...

    @abstractmethod
    async def list_categories(self, status: ProfileStatus) -> list[str]:
        """상태로 필터한 카테고리 목록(중복 제거, 가나다순)."""
        ...

    @abstractmethod
    async def list_pending_review(self, limit: int) -> list[CreatorProfile]:
        """심사 대기(PENDING) 목록 — 검색 조건(주문 수신 여부 등) 없이 상태만 본다(갭 #101)."""
        ...

    @abstractmethod
    async def update_status(
        self, profile_id: int, status: ProfileStatus, rejection_reason: str | None = None
    ) -> CreatorProfile | None:
        """심사·재심사 전이 — 반려 시 사유 저장, 승인·재심사(PENDING 복귀) 시 None으로 비운다."""
        """심사 상태 전이(허브 심사 계약용) — 대상 없으면 None."""
        ...

    @abstractmethod
    async def set_accepting_orders(
        self, user_id: int, accepting: bool
    ) -> CreatorProfile | None:
        """주문 수신 여부 전환(갭 #64) — 소유자 기준, 프로필 없으면 None."""
        ...

    @abstractmethod
    async def update_profile(
        self,
        user_id: int,
        name: str,
        tagline: str,
        bio: str,
        location: str | None,
        primary_category: str,
    ) -> CreatorProfile | None:
        """소유 계정 기준 내용 수정(슬러그·상태 불변) — 프로필 없으면 None."""
        ...
