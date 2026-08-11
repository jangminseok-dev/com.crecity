from __future__ import annotations

from creator.app.dtos.popular_profiles_dto import PopularProfilesQuery
from creator.app.dtos.profile_listing_dto import ProfileListingItem
from creator.app.ports.input.popular_profiles_use_case import PopularProfilesUseCase
from creator.app.ports.output.creator_package_repository import CreatorPackageRepository
from creator.app.ports.output.creator_profile_repository import CreatorProfileRepository
from creator.app.ports.output.portfolio_item_repository import PortfolioItemRepository
from creator.domain.entities.creator_profile_entity import ProfileStatus
from hub.app.ports.output.creator_popularity_port import CreatorPopularityPort
from hub.app.ports.output.creator_rating_port import CreatorRatingPort

_RECENT_DAYS = 7  # "이번 주 인기" — 최근 7일 주문 기준
_RANK_POOL_FACTOR = 3  # 미승인·프로필 없는 계정이 섞여도 limit을 채우도록 여유 조회


class PopularProfilesInteractor(PopularProfilesUseCase):

    def __init__(
        self,
        repository: CreatorProfileRepository,
        packages: CreatorPackageRepository,
        portfolio: PortfolioItemRepository,
        ratings: CreatorRatingPort,
        popularity: CreatorPopularityPort,
    ) -> None:
        self._repository = repository
        self._packages = packages
        self._portfolio = portfolio
        self._ratings = ratings
        self._popularity = popularity

    async def list_popular(self, query: PopularProfilesQuery) -> list[ProfileListingItem]:
        ranking = await self._popularity.top_creators_by_recent_orders(
            days=_RECENT_DAYS, limit=query.limit * _RANK_POOL_FACTOR
        )
        if not ranking:
            return []

        profiles = await self._repository.list_by_user_ids(
            user_ids=[rank.creator_user_id for rank in ranking], status=ProfileStatus.APPROVED
        )
        by_user_id = {p.user_id: p for p in profiles if p.user_id is not None}
        # 주문 수 내림차순(순위 순서) 유지, 승인 프로필만, limit개
        ordered = [
            by_user_id[rank.creator_user_id]
            for rank in ranking
            if rank.creator_user_id in by_user_id
        ][: query.limit]
        if not ordered:
            return []

        profile_ids = [p.id for p in ordered]
        user_ids = [p.user_id for p in ordered if p.user_id is not None]
        prices = await self._packages.min_prices_by_profile_ids(profile_ids)
        covers = await self._portfolio.first_file_names_by_profile_ids(profile_ids)
        ratings = await self._ratings.get_rating_summaries(user_ids)

        def to_item(profile) -> ProfileListingItem:
            rating = ratings.get(profile.user_id) if profile.user_id is not None else None
            return ProfileListingItem(
                id=profile.id,
                slug=profile.slug,
                name=profile.name,
                tagline=profile.tagline,
                location=profile.location,
                primary_category=profile.primary_category,
                created_at=profile.created_at,
                cover_file_name=covers.get(profile.id),
                price_from=prices.get(profile.id),
                rating_avg=rating.average_overall if rating else None,
                rating_count=rating.review_count if rating else 0,
            )

        return [to_item(profile) for profile in ordered]
