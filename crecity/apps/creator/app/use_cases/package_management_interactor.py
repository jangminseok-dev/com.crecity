from __future__ import annotations

from creator.app.dtos.package_management_dto import (
    PackageListQuery,
    PackageRegistrationCommand,
    PackageRemovalCommand,
    PackageResult,
    PackageUpdateCommand,
)
from creator.app.exceptions import PackageNotFoundError, ProfileNotFoundError
from creator.app.ports.input.package_management_use_case import PackageManagementUseCase
from creator.app.ports.output.creator_package_repository import CreatorPackageRepository
from creator.app.ports.output.creator_profile_repository import CreatorProfileRepository
from creator.domain.entities.creator_package_entity import CreatorPackage, PackagePlatform
from creator.domain.value_objects.price import Price


def _parse_platform(raw: str) -> PackagePlatform:
    try:
        return PackagePlatform(raw)
    except ValueError:
        allowed = ", ".join(p.value for p in PackagePlatform)
        raise ValueError(f"지원하지 않는 플랫폼입니다: {raw} (허용: {allowed})")


def _to_result(package: CreatorPackage) -> PackageResult:
    return PackageResult(
        id=package.id,
        profile_id=package.profile_id,
        platform=package.platform.value,
        title=package.title,
        description=package.description,
        price_krw=package.price_krw,
        created_at=package.created_at,
    )


class PackageManagementInteractor(PackageManagementUseCase):

    def __init__(
        self,
        profiles: CreatorProfileRepository,
        packages: CreatorPackageRepository,
    ) -> None:
        self._profiles = profiles
        self._packages = packages

    async def register(self, command: PackageRegistrationCommand) -> PackageResult:
        profile = await self._profiles.find_by_slug(command.slug)
        if profile is None:
            raise ProfileNotFoundError(f"프로필을 찾을 수 없습니다: {command.slug}")
        platform = _parse_platform(command.platform)
        price = Price(command.price_krw)
        package = await self._packages.create(
            profile_id=profile.id,
            platform=platform,
            title=command.title,
            description=command.description,
            price_krw=price.krw,
        )
        return _to_result(package)

    async def update(self, command: PackageUpdateCommand) -> PackageResult:
        platform = _parse_platform(command.platform)
        price = Price(command.price_krw)
        package = await self._packages.update(
            package_id=command.package_id,
            platform=platform,
            title=command.title,
            description=command.description,
            price_krw=price.krw,
        )
        if package is None:
            raise PackageNotFoundError(f"패키지를 찾을 수 없습니다: {command.package_id}")
        return _to_result(package)

    async def remove(self, command: PackageRemovalCommand) -> None:
        if not await self._packages.delete(command.package_id):
            raise PackageNotFoundError(f"패키지를 찾을 수 없습니다: {command.package_id}")

    async def list_for_profile(self, query: PackageListQuery) -> list[PackageResult]:
        profile = await self._profiles.find_by_slug(query.slug)
        if profile is None:
            raise ProfileNotFoundError(f"프로필을 찾을 수 없습니다: {query.slug}")
        packages = await self._packages.list_by_profile_id(profile.id)
        return [_to_result(package) for package in packages]
