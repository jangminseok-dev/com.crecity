import pytest

from creator.app.dtos.faq_management_dto import AddFaqCommand, RemoveFaqCommand
from creator.app.exceptions import (
    FaqLimitExceededError,
    FaqNotFoundError,
    ProfileNotFoundError,
)
from creator.app.use_cases.faq_management_interactor import FaqManagementInteractor
from creator.domain.entities.creator_profile_entity import CreatorProfile, ProfileStatus
from creator.domain.entities.profile_faq_entity import MAX_FAQ_PER_PROFILE, ProfileFaq

OWNER = 100
_PROFILE = CreatorProfile(
    id=1, slug="kim-beauty", name="김뷰티", tagline="뷰티 크리에이터",
    bio="소개", location="서울", primary_category="뷰티",
    status=ProfileStatus.APPROVED, user_id=OWNER,
)


class _StubProfileRepository:
    def __init__(self, profile=_PROFILE):
        self.profile = profile

    async def find_by_user_id(self, user_id):
        return self.profile if self.profile and self.profile.user_id == user_id else None

    async def find_by_slug(self, slug):
        return self.profile if self.profile and self.profile.slug == slug else None


class _StubFaqRepository:
    def __init__(self):
        self.rows: list[ProfileFaq] = []

    async def add(self, profile_id, question, answer):
        faq = ProfileFaq(id=len(self.rows) + 1, profile_id=profile_id, question=question, answer=answer)
        self.rows.append(faq)
        return faq

    async def list_by_profile_id(self, profile_id):
        return [f for f in self.rows if f.profile_id == profile_id]

    async def count_by_profile_id(self, profile_id):
        return len([f for f in self.rows if f.profile_id == profile_id])

    async def delete(self, profile_id, faq_id):
        before = len(self.rows)
        self.rows = [f for f in self.rows if not (f.id == faq_id and f.profile_id == profile_id)]
        return len(self.rows) < before


def _interactor(profile=_PROFILE):
    faqs = _StubFaqRepository()
    return FaqManagementInteractor(profiles=_StubProfileRepository(profile), faqs=faqs), faqs


def _command(question="오디언스는 어떤 분들인가요?", answer="20~30대 여성이 70%입니다."):
    return AddFaqCommand(requester_user_id=OWNER, question=question, answer=answer)


async def test_FAQ를_추가하면_목록에_담긴다():
    interactor, faqs = _interactor()
    result = await interactor.add(_command())
    assert result.question == "오디언스는 어떤 분들인가요?"
    assert len(faqs.rows) == 1


async def test_질문이나_답변이_비면_ValueError():
    interactor, _ = _interactor()
    with pytest.raises(ValueError):
        await interactor.add(_command(question="   "))
    with pytest.raises(ValueError):
        await interactor.add(_command(answer=""))


async def test_상한을_넘으면_FaqLimitExceededError():
    interactor, _ = _interactor()
    for index in range(MAX_FAQ_PER_PROFILE):
        await interactor.add(_command(question=f"질문 {index}"))
    with pytest.raises(FaqLimitExceededError):
        await interactor.add(_command(question="하나 더"))


async def test_프로필이_없으면_ProfileNotFoundError():
    interactor, _ = _interactor(profile=None)
    with pytest.raises(ProfileNotFoundError):
        await interactor.add(_command())


async def test_삭제하고_없는_FAQ_삭제는_404():
    interactor, _ = _interactor()
    created = await interactor.add(_command())
    await interactor.remove(RemoveFaqCommand(requester_user_id=OWNER, faq_id=created.id))
    with pytest.raises(FaqNotFoundError):
        await interactor.remove(RemoveFaqCommand(requester_user_id=OWNER, faq_id=created.id))


async def test_공개_목록은_슬러그로_조회한다():
    interactor, _ = _interactor()
    await interactor.add(_command())
    results = await interactor.list_public("kim-beauty")
    assert len(results) == 1
