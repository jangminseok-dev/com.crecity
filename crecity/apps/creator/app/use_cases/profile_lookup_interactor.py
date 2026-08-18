from __future__ import annotations

from creator.app.dtos.profile_lookup_dto import ProfileLookupQuery, ProfileLookupResult
from creator.app.exceptions import ProfileNotFoundError
from creator.app.ports.input.profile_lookup_use_case import ProfileLookupUseCase
from creator.app.ports.output.analytics_repository import AnalyticsRepository
from creator.app.ports.output.creator_profile_repository import CreatorProfileRepository
from hub.app.ports.output.creator_trade_stats_port import CreatorTradeStatsPort
from creator.domain.entities.creator_profile_entity import ProfileStatus
from creator.domain.value_objects.trust_check import is_trusted_creator


class ProfileLookupInteractor(ProfileLookupUseCase):

    def __init__(
        self,
        repository: CreatorProfileRepository,
        analytics: AnalyticsRepository,
        trade_stats: CreatorTradeStatsPort,
        trust_min_verified_channels: int,
        trust_min_completed_orders: int,
    ) -> None:
        self._repository = repository
        self._analytics = analytics
        self._trade_stats = trade_stats
        self._trust_min_verified_channels = trust_min_verified_channels
        self._trust_min_completed_orders = trust_min_completed_orders

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
        # 신뢰 배지(갭 #81) — 채널 지표는 스크린샷이 필수라 등록 채널 수 = 인증 채널 수
        verified_channels = len(await self._analytics.list_by_profile_id(profile.id))
        trusted = stats is not None and is_trusted_creator(
            verified_channels=verified_channels,
            completed_orders=stats.completed_orders,
            accept_expired_orders=stats.accept_expired_orders,
            dispute_refund_orders=stats.dispute_refund_orders,
            min_verified_channels=self._trust_min_verified_channels,
            min_completed_orders=self._trust_min_completed_orders,
        )
        return ProfileLookupResult(
            trusted_creator=trusted,
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
