import pytest

from creator.app.dtos.package_management_dto import (
    PackageListQuery,
    PackageRegistrationCommand,
    PackageRemovalCommand,
    PackageUpdateCommand,
)
from creator.app.exceptions import PackageNotFoundError, ProfileNotFoundError
from creator.app.use_cases.package_management_interactor import PackageManagementInteractor
from creator.domain.entities.creator_package_entity import CreatorPackage, PackagePlatform
from creator.domain.entities.creator_profile_entity import CreatorProfile, ProfileStatus


class _StubProfileRepository:
    def __init__(self, profile: CreatorProfile | None):
        self.profile = profile

    async def create(self, **kwargs):
        raise NotImplementedError

    async def find_by_slug(self, slug):
        return self.profile if self.profile and self.profile.slug == slug else None

    async def exists_by_slug(self, slug):
        return self.profile is not None and self.profile.slug == slug


class _StubPackageRepository:
    def __init__(self, packages: list[CreatorPackage] | None = None):
        self.packages = {p.id: p for p in (packages or [])}
        self._next_id = max(self.packages, default=0) + 1

    async def create(self, profile_id, platform, title, description, price_krw):
        package = CreatorPackage(
            id=self._next_id,
            profile_id=profile_id,
            platform=platform,
            title=title,
            description=description,
            price_krw=price_krw,
        )
        self.packages[package.id] = package
        self._next_id += 1
        return package

    async def update(self, package_id, platform, title, description, price_krw):
        if package_id not in self.packages:
            return None
        existing = self.packages[package_id]
        updated = CreatorPackage(
            id=package_id,
            profile_id=existing.profile_id,
            platform=platform,
            title=title,
            description=description,
            price_krw=price_krw,
        )
        self.packages[package_id] = updated
        return updated

    async def delete(self, package_id):
        return self.packages.pop(package_id, None) is not None

    async def list_by_profile_id(self, profile_id):
        found = [p for p in self.packages.values() if p.profile_id == profile_id]
        return sorted(found, key=lambda p: p.price_krw)


_PROFILE = CreatorProfile(
    id=1,
    slug="kim-beauty",
    name="김뷰티",
    tagline="스킨케어 리뷰",
    bio="소개",
    location="서울",
    primary_category="뷰티",
    status=ProfileStatus.APPROVED,
)


def _package(id=1, price_krw=300000, platform=PackagePlatform.INSTAGRAM):
    return CreatorPackage(
        id=id,
        profile_id=1,
        platform=platform,
        title="릴스 1개",
        description="수정 2회 포함",
        price_krw=price_krw,
    )


def _register_command(platform="INSTAGRAM", price_krw=300000, slug="kim-beauty"):
    return PackageRegistrationCommand(
        slug=slug, platform=platform, title="릴스 1개",
        description="수정 2회 포함", price_krw=price_krw,
    )


def _interactor(profile=_PROFILE, packages=None):
    return PackageManagementInteractor(
        profiles=_StubProfileRepository(profile),
        packages=_StubPackageRepository(packages),
    )


async def test_등록하면_프로필에_귀속된_패키지가_생성된다():
    result = await _interactor().register(_register_command())
    assert result.profile_id == 1
    assert result.platform == "INSTAGRAM"


async def test_없는_프로필에_등록하면_ProfileNotFoundError():
    with pytest.raises(ProfileNotFoundError):
        await _interactor(profile=None).register(_register_command())


async def test_지원하지_않는_플랫폼이면_ValueError():
    with pytest.raises(ValueError):
        await _interactor().register(_register_command(platform="FACEBOOK"))


async def test_가격이_0이하면_ValueError():
    with pytest.raises(ValueError):
        await _interactor().register(_register_command(price_krw=0))


async def test_수정하면_변경값이_반영된다():
    interactor = _interactor(packages=[_package()])
    result = await interactor.update(
        PackageUpdateCommand(
            package_id=1, platform="UGC", title="UGC 사진 4장",
            description="원본 제공", price_krw=200000,
        )
    )
    assert result.platform == "UGC"
    assert result.price_krw == 200000


async def test_없는_패키지_수정이면_PackageNotFoundError():
    with pytest.raises(PackageNotFoundError):
        await _interactor().update(
            PackageUpdateCommand(
                package_id=99, platform="UGC", title="t", description="d", price_krw=1000,
            )
        )


async def test_삭제하면_목록에서_사라진다():
    interactor = _interactor(packages=[_package()])
    await interactor.remove(PackageRemovalCommand(package_id=1))
    assert await interactor.list_for_profile(PackageListQuery(slug="kim-beauty")) == []


async def test_없는_패키지_삭제면_PackageNotFoundError():
    with pytest.raises(PackageNotFoundError):
        await _interactor().remove(PackageRemovalCommand(package_id=99))


async def test_목록은_가격_오름차순이다():
    interactor = _interactor(
        packages=[_package(id=1, price_krw=500000), _package(id=2, price_krw=175000)]
    )
    results = await interactor.list_for_profile(PackageListQuery(slug="kim-beauty"))
    assert [r.price_krw for r in results] == [175000, 500000]
