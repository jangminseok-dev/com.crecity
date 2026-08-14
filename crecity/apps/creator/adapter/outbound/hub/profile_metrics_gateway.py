from __future__ import annotations

from core.database import session_scope
from creator.adapter.outbound.pg.creator_profile_pg_repository import CreatorProfilePgRepository
from creator.domain.entities.creator_profile_entity import ProfileStatus
from hub.app.dtos.platform_metrics_dto import ProfileMetrics
from hub.app.ports.output.platform_metrics_port import ProfileMetricsPort


class CreatorProfileMetricsGateway(ProfileMetricsPort):
    """허브 ProfileMetricsPort 계약의 creator 구현(운영 대시보드, 갭 #55).

    DELETED(탈퇴 표식)는 세지 않는다 — 심사 현황이 관심사다.
    """

    async def get_profile_metrics(self) -> ProfileMetrics:
        async with session_scope() as session:
            repository = CreatorProfilePgRepository(session)
            counts = {
                status: await repository.count_by_status(status=status, category=None)
                for status in (ProfileStatus.PENDING, ProfileStatus.APPROVED, ProfileStatus.REJECTED)
            }
        return ProfileMetrics(
            pending_review=counts[ProfileStatus.PENDING],
            approved=counts[ProfileStatus.APPROVED],
            rejected=counts[ProfileStatus.REJECTED],
        )
