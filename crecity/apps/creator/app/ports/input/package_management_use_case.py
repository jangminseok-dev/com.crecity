from __future__ import annotations

from abc import ABC, abstractmethod

from creator.app.dtos.package_management_dto import (
    PackageListQuery,
    PackageRegistrationCommand,
    PackageRemovalCommand,
    PackageResult,
    PackageUpdateCommand,
)


class PackageManagementUseCase(ABC):
    """패키지 관리 유스케이스 — 가격 공개 상품의 등록·수정·삭제·목록.

    소유권 검증(본인 패키지만 수정/삭제)은 auth 도입 시 추가한다(BOUNDARIES §7-2 순서).
    """

    @abstractmethod
    async def register(self, command: PackageRegistrationCommand) -> PackageResult:
        """프로필에 패키지를 등록한다.

        Raises:
            ProfileNotFoundError: 슬러그의 프로필 없음.
            ValueError: 플랫폼·가격 형식 위반.
        """
        ...

    @abstractmethod
    async def update(self, command: PackageUpdateCommand) -> PackageResult:
        """패키지를 수정한다.

        Raises:
            PackageNotFoundError: 대상 패키지 없음.
            ValueError: 플랫폼·가격 형식 위반.
        """
        ...

    @abstractmethod
    async def remove(self, command: PackageRemovalCommand) -> None:
        """패키지를 삭제한다.

        Raises:
            PackageNotFoundError: 대상 패키지 없음.
        """
        ...

    @abstractmethod
    async def list_for_profile(self, query: PackageListQuery) -> list[PackageResult]:
        """프로필의 패키지 목록(가격 오름차순 — 사이드바 최저가 표시용).

        Raises:
            ProfileNotFoundError: 슬러그의 프로필 없음.
        """
        ...
