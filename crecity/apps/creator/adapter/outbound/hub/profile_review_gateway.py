from __future__ import annotations

from core.database import session_scope
from creator.adapter.outbound.pg.creator_profile_pg_repository import CreatorProfilePgRepository
from creator.domain.entities.creator_profile_entity import CreatorProfile, ProfileStatus
from hub.app.dtos.profile_review_dto import ProfileReviewSummary
from hub.app.ports.output.profile_review_port import ProfileReviewPort

# 심사 목록 상한 — 한 화면 분량(더 쌓이면 처리 후 재조회)
_PENDING_LIMIT = 50


def _to_summary(profile: CreatorProfile) -> ProfileReviewSummary:
    return ProfileReviewSummary(
        id=profile.id,
        slug=profile.slug,
        name=profile.name,
        tagline=profile.tagline,
        bio=profile.bio,
        primary_category=profile.primary_category,
        status=profile.status.value,
        created_at=profile.created_at,
    )


class CreatorProfileReviewGateway(ProfileReviewPort):
    """허브 ProfileReviewPort 계약의 creator 구현 — main.py가 조립한다."""

    async def list_pending_profiles(self) -> list[ProfileReviewSummary]:
        async with session_scope() as session:
            profiles = await CreatorProfilePgRepository(session).list_by_status(
                status=ProfileStatus.PENDING, category=None, limit=_PENDING_LIMIT, offset=0
            )
        # list_by_status는 최신순 — 심사는 오래 기다린 순서가 공정하다
        return [_to_summary(profile) for profile in reversed(profiles)]

    async def review_profile(self, profile_id: int, approved: bool) -> ProfileReviewSummary | None:
        status = ProfileStatus.APPROVED if approved else ProfileStatus.REJECTED
        async with session_scope() as session:
            profile = await CreatorProfilePgRepository(session).update_status(profile_id, status)
        return _to_summary(profile) if profile is not None else None
