from __future__ import annotations

from creator.app.dtos.faq_management_dto import AddFaqCommand, FaqResult, RemoveFaqCommand
from creator.app.exceptions import (
    FaqLimitExceededError,
    FaqNotFoundError,
    ProfileNotFoundError,
)
from creator.app.ports.input.faq_management_use_case import FaqManagementUseCase
from creator.app.ports.output.creator_profile_repository import CreatorProfileRepository
from creator.app.ports.output.faq_repository import FaqRepository
from creator.domain.entities.creator_profile_entity import CreatorProfile
from creator.domain.entities.profile_faq_entity import MAX_FAQ_PER_PROFILE

_MAX_QUESTION = 200
_MAX_ANSWER = 2000


class FaqManagementInteractor(FaqManagementUseCase):

    def __init__(self, profiles: CreatorProfileRepository, faqs: FaqRepository) -> None:
        self._profiles = profiles
        self._faqs = faqs

    async def _my_profile(self, requester_user_id: int) -> CreatorProfile:
        profile = await self._profiles.find_by_user_id(requester_user_id)
        if profile is None:
            raise ProfileNotFoundError("프로필을 먼저 등록해 주세요.")
        return profile

    async def add(self, command: AddFaqCommand) -> FaqResult:
        question, answer = command.question.strip(), command.answer.strip()
        if not question or not answer:
            raise ValueError("질문과 답변을 모두 입력해 주세요.")
        if len(question) > _MAX_QUESTION or len(answer) > _MAX_ANSWER:
            raise ValueError(f"질문은 {_MAX_QUESTION}자, 답변은 {_MAX_ANSWER}자 이하여야 합니다.")

        profile = await self._my_profile(command.requester_user_id)
        if await self._faqs.count_by_profile_id(profile.id) >= MAX_FAQ_PER_PROFILE:
            raise FaqLimitExceededError(f"FAQ는 최대 {MAX_FAQ_PER_PROFILE}개까지 등록할 수 있습니다.")
        faq = await self._faqs.add(profile.id, question, answer)
        return FaqResult.from_entity(faq)

    async def list_mine(self, requester_user_id: int) -> list[FaqResult]:
        profile = await self._my_profile(requester_user_id)
        return [FaqResult.from_entity(f) for f in await self._faqs.list_by_profile_id(profile.id)]

    async def remove(self, command: RemoveFaqCommand) -> None:
        profile = await self._my_profile(command.requester_user_id)
        if not await self._faqs.delete(profile.id, command.faq_id):
            raise FaqNotFoundError(f"FAQ를 찾을 수 없습니다: {command.faq_id}")

    async def list_public(self, slug: str) -> list[FaqResult]:
        profile = await self._profiles.find_by_slug(slug)
        if profile is None:
            raise ProfileNotFoundError(f"프로필을 찾을 수 없습니다: {slug}")
        return [FaqResult.from_entity(f) for f in await self._faqs.list_by_profile_id(profile.id)]
