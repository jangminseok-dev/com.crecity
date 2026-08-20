import pytest

from creator.app.dtos.profile_update_dto import ProfileUpdateCommand
from creator.app.exceptions import ProfileNotFoundError
from creator.app.use_cases.profile_update_interactor import ProfileUpdateInteractor
from creator.domain.entities.creator_profile_entity import CreatorProfile, ProfileStatus


class _StubRepository:
    def __init__(self, profile: CreatorProfile | None):
        self.profile = profile
        self.updates = []

    async def update_profile(self, user_id, name, tagline, bio, location, primary_category):
        self.updates.append(user_id)
        if self.profile is None or self.profile.user_id != user_id:
            return None
        return CreatorProfile(
            id=self.profile.id,
            slug=self.profile.slug,  # 슬러그 불변
            name=name,
            tagline=tagline,
            bio=bio,
            location=location,
            primary_category=primary_category,
            status=self.profile.status,  # 상태 유지
            user_id=user_id,
            accepting_orders=self.profile.accepting_orders,
        )


def _profile():
    return CreatorProfile(
        id=1, slug="kim-beauty", name="김뷰티", tagline="스킨케어", bio="소개",
        location="서울", primary_category="뷰티", status=ProfileStatus.APPROVED, user_id=7,
    )


def _command(user_id=7):
    return ProfileUpdateCommand(
        user_id=user_id, name="김뷰티2", tagline="새 소개", bio="새 상세",
        location=None, primary_category="라이프",
    )


async def test_수정해도_슬러그와_심사_상태는_유지된다():
    interactor = ProfileUpdateInteractor(_StubRepository(_profile()))
    result = await interactor.update_my_profile(_command())
    assert result.slug == "kim-beauty"
    assert result.status == "APPROVED"
    assert result.name == "김뷰티2"
    assert result.primary_category == "라이프"


async def test_주문_수신_여부가_실제_값으로_실린다():
    # 회귀 고정: DTO 기본값(True)이 실제 값(False)을 덮어 응답이 거짓이 되던 경로(갭 #100 종단에서 발견)
    profile = _profile()
    from dataclasses import replace
    interactor = ProfileUpdateInteractor(_StubRepository(replace(profile, accepting_orders=False)))
    result = await interactor.update_my_profile(_command())
    assert result.accepting_orders is False


async def test_새_카테고리도_허용된다():
    # 갭 #100 — 세분화로 추가된 카테고리
    interactor = ProfileUpdateInteractor(_StubRepository(_profile()))
    command = ProfileUpdateCommand(
        user_id=7, name="김뷰티", tagline="소개", bio="상세", location=None,
        primary_category="육아",
    )
    result = await interactor.update_my_profile(command)
    assert result.primary_category == "육아"


async def test_프로필이_없으면_ProfileNotFoundError():
    interactor = ProfileUpdateInteractor(_StubRepository(None))
    with pytest.raises(ProfileNotFoundError):
        await interactor.update_my_profile(_command(user_id=99))
