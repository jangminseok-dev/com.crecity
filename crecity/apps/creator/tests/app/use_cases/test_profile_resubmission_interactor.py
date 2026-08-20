import pytest

from creator.app.dtos.profile_resubmission_dto import ProfileResubmissionCommand
from creator.app.exceptions import NotRejectedProfileError, ProfileNotFoundError
from creator.app.use_cases.profile_resubmission_interactor import ProfileResubmissionInteractor
from creator.domain.entities.creator_profile_entity import CreatorProfile, ProfileStatus


class _StubRepository:
    def __init__(self, profile: CreatorProfile | None):
        self.profile = profile
        self.updates: list[tuple[int, ProfileStatus, str | None]] = []

    async def find_by_user_id(self, user_id):
        return self.profile if self.profile and self.profile.user_id == user_id else None

    async def update_status(self, profile_id, status, rejection_reason=None):
        self.updates.append((profile_id, status, rejection_reason))
        from dataclasses import replace

        return replace(self.profile, status=status, rejection_reason=rejection_reason)


def _profile(status=ProfileStatus.REJECTED, reason="포트폴리오가 비어 있습니다"):
    return CreatorProfile(
        id=1, slug="kim-beauty", name="김뷰티", tagline="소개", bio="상세",
        location=None, primary_category="뷰티", status=status, user_id=7,
        rejection_reason=reason if status is ProfileStatus.REJECTED else None,
    )


async def test_반려_프로필은_대기로_복귀하고_사유가_비워진다():
    repository = _StubRepository(_profile())
    result = await ProfileResubmissionInteractor(repository).resubmit(
        ProfileResubmissionCommand(user_id=7)
    )
    assert repository.updates == [(1, ProfileStatus.PENDING, None)]
    assert result.status == "PENDING"
    assert result.rejection_reason is None


async def test_반려_상태가_아니면_409_예외():
    for status in (ProfileStatus.PENDING, ProfileStatus.APPROVED):
        repository = _StubRepository(_profile(status=status))
        with pytest.raises(NotRejectedProfileError):
            await ProfileResubmissionInteractor(repository).resubmit(
                ProfileResubmissionCommand(user_id=7)
            )


async def test_프로필이_없으면_404_예외():
    with pytest.raises(ProfileNotFoundError):
        await ProfileResubmissionInteractor(_StubRepository(None)).resubmit(
            ProfileResubmissionCommand(user_id=7)
        )
