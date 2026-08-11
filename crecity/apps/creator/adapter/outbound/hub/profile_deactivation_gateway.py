from __future__ import annotations

from core.database import session_scope
from creator.adapter.outbound.pg.creator_profile_pg_repository import CreatorProfilePgRepository
from creator.domain.entities.creator_profile_entity import ProfileStatus
from hub.app.ports.output.profile_deactivation_port import ProfileDeactivationPort


class CreatorProfileDeactivationGateway(ProfileDeactivationPort):
    """허브 ProfileDeactivationPort 계약의 creator 구현 — main.py가 조립한다."""

    async def deactivate_profile(self, user_id: int) -> None:
        async with session_scope() as session:
            repository = CreatorProfilePgRepository(session)
            profile = await repository.find_by_user_id(user_id)
            if profile is None:  # 브랜드 계정 등 프로필이 없는 사용자
                return
            await repository.update_status(profile.id, ProfileStatus.DELETED)
