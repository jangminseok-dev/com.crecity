from __future__ import annotations

from abc import ABC, abstractmethod

from creator.domain.entities.creator_package_entity import CreatorPackage, PackagePlatform


class CreatorPackageRepository(ABC):
    """패키지 영속성 포트 (도메인어 명명 예외)."""

    @abstractmethod
    async def create(
        self,
        profile_id: int,
        platform: PackagePlatform,
        title: str,
        description: str,
        price_krw: int,
    ) -> CreatorPackage: ...

    @abstractmethod
    async def find_by_id(self, package_id: int) -> CreatorPackage | None:
        """소유권 검증용 조회 — 수정·삭제 전에 소속 프로필을 확인한다."""
        ...

    @abstractmethod
    async def update(
        self,
        package_id: int,
        platform: PackagePlatform,
        title: str,
        description: str,
        price_krw: int,
    ) -> CreatorPackage | None:
        """수정 후 결과 반환 — 대상 없으면 None."""
        ...

    @abstractmethod
    async def delete(self, package_id: int) -> bool:
        """삭제 성공 여부 — 대상 없으면 False."""
        ...

    @abstractmethod
    async def list_by_profile_id(self, profile_id: int) -> list[CreatorPackage]: ...

    @abstractmethod
    async def min_prices_by_profile_ids(self, profile_ids: list[int]) -> dict[int, int]:
        """프로필별 최저 패키지 가격(목록 카드 '부터' 가격) — 패키지 없는 프로필은 키 부재."""
        ...
