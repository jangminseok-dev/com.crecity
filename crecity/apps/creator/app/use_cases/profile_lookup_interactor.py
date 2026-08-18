from __future__ import annotations

from creator.app.dtos.profile_lookup_dto import ProfileLookupQuery, ProfileLookupResult
from creator.app.exceptions import ProfileNotFoundError
from creator.app.ports.input.profile_lookup_use_case import ProfileLookupUseCase
from creator.app.ports.output.analytics_repository import AnalyticsRepository
from creator.app.ports.output.creator_profile_repository import CreatorProfileRepository
from hub.app.ports.output.creator_trade_stats_port import CreatorTradeStatsPort
from creator.domain.entities.creator_profile_entity import ProfileStatus


class ProfileLookupInteractor(ProfileLookupUseCase):

    def __init__(
        self,
        repository: CreatorProfileRepository,
        analytics: AnalyticsRepository,
        trade_stats: CreatorTradeStatsPort,
    ) -> None:
        self._repository = repository
        self._analytics = analytics
        self._trade_stats = trade_stats

    async def lookup(self, query: ProfileLookupQuery) -> ProfileLookupResult:
        profile = await self._repository.find_by_slug(query.slug)
        if profile is None or profile.status is ProfileStatus.DELETED:
            raise ProfileNotFoundError(f"프로필을 찾을 수 없습니다: {query.slug}")
        # 거래 실적은 order 소유라 허브 계약으로 읽는다(갭 #66)
        stats = (
            await self._trade_stats.get_creator_stats(profile.user_id)
            if profile.user_id is not None
            else None
        )
        has_history = stats is not None and stats.received_orders > 0
        return ProfileLookupResult(
            followers_total=await self._analytics.followers_total(profile.id),
            completed_orders=stats.completed_orders if has_history else None,
            accepted_orders=stats.accepted_orders if has_history else None,
            received_orders=stats.received_orders if has_history else None,
            # 응답 지표(갭 #80)는 이력 표본 유무를 order가 판단한다(None/False로 온다)
            avg_accept_hours=stats.avg_accept_hours if stats is not None else None,
            fast_responder=stats.fast_responder if stats is not None else False,
            id=profile.id,
            slug=profile.slug,
            name=profile.name,
            tagline=profile.tagline,
            bio=profile.bio,
            location=profile.location,
            primary_category=profile.primary_category,
            status=profile.status.value,
            accepting_orders=profile.accepting_orders,
            created_at=profile.created_at,
        )
