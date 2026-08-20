from __future__ import annotations

from creator.app.dtos.my_profile_lookup_dto import MyProfileResult
from creator.app.dtos.profile_resubmission_dto import ProfileResubmissionCommand
from creator.app.exceptions import NotRejectedProfileError, ProfileNotFoundError
from creator.app.ports.input.profile_resubmission_use_case import ProfileResubmissionUseCase
from creator.app.ports.output.creator_profile_repository import CreatorProfileRepository
from creator.domain.entities.creator_profile_entity import ProfileStatus


class ProfileResubmissionInteractor(ProfileResubmissionUseCase):

    def __init__(self, repository: CreatorProfileRepository) -> None:
        self._repository = repository

    async def resubmit(self, command: ProfileResubmissionCommand) -> MyProfileResult:
        profile = await self._repository.find_by_user_id(command.user_id)
        if profile is None:
            raise ProfileNotFoundError("등록된 프로필이 없습니다.")
        # 반려 상태에서만 — 대기·승인 프로필의 재심사는 의미가 없고 심사 큐만 오염시킨다
        if profile.status is not ProfileStatus.REJECTED:
            raise NotRejectedProfileError("반려된 프로필만 재심사를 요청할 수 있습니다.")
        # PENDING 복귀 + 사유 초기화 — 심사 큐(list_pending_review)에 다시 들어간다
        updated = await self._repository.update_status(
            profile.id, ProfileStatus.PENDING, rejection_reason=None
        )
        if updated is None:  # find 직후라 실질적으로 도달하지 않는 경로
            raise ProfileNotFoundError("등록된 프로필이 없습니다.")
        return MyProfileResult(
            id=updated.id,
            slug=updated.slug,
            name=updated.name,
            tagline=updated.tagline,
            bio=updated.bio,
            location=updated.location,
            primary_category=updated.primary_category,
            status=updated.status.value,
            created_at=updated.created_at,
            accepting_orders=updated.accepting_orders,
            rejection_reason=updated.rejection_reason,
        )
