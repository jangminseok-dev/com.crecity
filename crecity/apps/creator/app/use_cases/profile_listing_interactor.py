from __future__ import annotations

from creator.app.dtos.profile_listing_dto import (
    ProfileListingItem,
    ProfileListingQuery,
    ProfileListingResult,
)
from creator.app.ports.input.profile_listing_use_case import ProfileListingUseCase
from creator.app.ports.output.creator_package_repository import CreatorPackageRepository
from creator.app.ports.output.creator_profile_repository import CreatorProfileRepository
from creator.app.ports.output.portfolio_item_repository import PortfolioItemRepository
from creator.domain.entities.creator_profile_entity import ProfileStatus
from hub.app.ports.output.creator_rating_port import CreatorRatingPort


class ProfileListingInteractor(ProfileListingUseCase):

    def __init__(
        self,
        repository: CreatorProfileRepository,
        packages: CreatorPackageRepository,
        portfolio: PortfolioItemRepository,
        ratings: CreatorRatingPort,
    ) -> None:
        self._repository = repository
        self._packages = packages
        self._portfolio = portfolio
        self._ratings = ratings

    async def list_profiles(self, query: ProfileListingQuery) -> ProfileListingResult:
        profiles = await self._repository.list_by_status(
            status=ProfileStatus.APPROVED,
            category=query.category,
            limit=query.limit,
            offset=query.offset,
            q=query.q,
            platform=query.platform,
            price_min=query.price_min,
            price_max=query.price_max,
            location=query.location,
        )
        total = await self._repository.count_by_status(
            status=ProfileStatus.APPROVED,
            category=query.category,
            q=query.q,
            platform=query.platform,
            price_min=query.price_min,
            price_max=query.price_max,
            location=query.location,
        )

        # 카드 보강 — 같은 스포크(패키지·포트폴리오)는 리포지토리, 평점은 허브(review 구현)
        profile_ids = [profile.id for profile in profiles]
        user_ids = [profile.user_id for profile in profiles if profile.user_id is not None]
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

        return ProfileListingResult(items=[to_item(p) for p in profiles], total=total)

    async def list_categories(self) -> list[str]:
        return await self._repository.list_categories(status=ProfileStatus.APPROVED)
