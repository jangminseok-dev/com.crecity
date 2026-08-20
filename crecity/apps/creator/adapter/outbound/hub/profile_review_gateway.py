from __future__ import annotations

from dataclasses import replace

from core.config import VETTING_MIN_ENGAGEMENT_PERMILLE, VETTING_MIN_FOLLOWERS
from core.database import session_scope
from creator.adapter.outbound.pg.analytics_pg_repository import AnalyticsPgRepository
from creator.adapter.outbound.pg.creator_profile_pg_repository import CreatorProfilePgRepository
from creator.domain.entities.creator_profile_entity import CreatorProfile, ProfileStatus
from creator.domain.value_objects.vetting_check import VettingCheck
from hub.adapter.outbound.pg.outbox_pg_store import enqueue_events
from hub.app.dtos.outbox_event_dto import OutboxEvent
from hub.app.dtos.profile_review_dto import FlaggedAnalyticsSummary, ProfileReviewSummary
from hub.app.ports.output.profile_review_port import ProfileReviewPort

# 심사 목록 상한 — 한 화면 분량(더 쌓이면 처리 후 재조회)
_PENDING_LIMIT = 50


def _to_summary(
    profile: CreatorProfile, check: VettingCheck | None = None
) -> ProfileReviewSummary:
    summary = ProfileReviewSummary(
        id=profile.id,
        slug=profile.slug,
        name=profile.name,
        tagline=profile.tagline,
        bio=profile.bio,
        primary_category=profile.primary_category,
        status=profile.status.value,
        created_at=profile.created_at,
    )
    if check is None:
        return summary
    return replace(
        summary,
        platform_count=check.platform_count,
        total_followers=check.total_followers,
        best_engagement_permille=check.best_engagement_permille,
        min_followers=check.min_followers,
        min_engagement_permille=check.min_engagement_permille,
        vetting_passed=check.passed,
    )


class CreatorProfileReviewGateway(ProfileReviewPort):
    """허브 ProfileReviewPort 계약의 creator 구현 — main.py가 조립한다."""

    async def list_pending_profiles(self) -> list[ProfileReviewSummary]:
        async with session_scope() as session:
            # 검색용 list_by_status(주문 수신 중 조건 포함)를 쓰면 수신을 끈 PENDING이
            # 심사 큐에서 누락된다 — 심사는 상태만 본다(갭 #101에서 발견·수정)
            profiles = await CreatorProfilePgRepository(session).list_pending_review(
                limit=_PENDING_LIMIT
            )
            analytics = AnalyticsPgRepository(session)
            checks = {
                profile.id: VettingCheck.of(
                    await analytics.list_by_profile_id(profile.id),
                    min_followers=VETTING_MIN_FOLLOWERS,
                    min_engagement_permille=VETTING_MIN_ENGAGEMENT_PERMILLE,
                )
                for profile in profiles
            }
        # list_pending_review가 등록 오래된 순 — 오래 기다린 순서가 공정하다
        return [_to_summary(profile, checks[profile.id]) for profile in profiles]

    async def review_profile(
        self, profile_id: int, approved: bool, reason: str | None = None
    ) -> ProfileReviewSummary | None:
        status = ProfileStatus.APPROVED if approved else ProfileStatus.REJECTED
        rejection_reason = None if approved else reason
        async with session_scope() as session:
            repository = CreatorProfilePgRepository(session)
            target = await repository.find_by_id(profile_id)
            if target is None:
                return None
            # 이벤트를 먼저 세션에 적재 — update_status의 커밋에 함께 실린다(단일 트랜잭션)
            if target.user_id is not None:
                enqueue_events(
                    session,
                    [
                        OutboxEvent(
                            event_type="profile.approved" if approved else "profile.rejected",
                            payload={
                                "profile_id": profile_id,
                                "creator_user_id": target.user_id,
                                "slug": target.slug,
                                "name": target.name,
                                # 반려 사유(갭 #101) — 알림 문구에 동봉된다
                                "reason": rejection_reason,
                            },
                        )
                    ],
                )
            profile = await repository.update_status(
                profile_id, status, rejection_reason=rejection_reason
            )
        return _to_summary(profile) if profile is not None else None

    async def list_flagged_analytics(self) -> list[FlaggedAnalyticsSummary]:
        async with session_scope() as session:
            return await AnalyticsPgRepository(session).list_flagged()

    async def clear_analytics_flag(self, analytics_id: int) -> bool:
        async with session_scope() as session:
            return await AnalyticsPgRepository(session).clear_flag(analytics_id)
