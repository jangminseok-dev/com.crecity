from __future__ import annotations

from creator.app.dtos.profile_listing_dto import ProfileListingItem
from creator.app.dtos.similar_profiles_dto import SimilarProfilesQuery
from creator.app.exceptions import ProfileNotFoundError
from creator.app.ports.input.similar_profiles_use_case import SimilarProfilesUseCase
from creator.app.ports.output.creator_package_repository import CreatorPackageRepository
from creator.app.ports.output.creator_profile_repository import CreatorProfileRepository
from creator.app.ports.output.portfolio_item_repository import PortfolioItemRepository
from creator.domain.entities.creator_profile_entity import ProfileStatus
from creator.domain.value_objects.similarity import SimilarityCandidate, rank_similar
from hub.app.ports.output.creator_rating_port import CreatorRatingPort

_CANDIDATE_POOL = 50  # 같은 카테고리 후보 풀 상한 — 초과분은 순위 계산에서 빠진다(현 규모엔 충분)


class SimilarProfilesInteractor(SimilarProfilesUseCase):

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

    async def list_similar(self, query: SimilarProfilesQuery) -> list[ProfileListingItem]:
        target = await self._repository.find_by_slug(query.slug)
        if target is None or target.status is ProfileStatus.DELETED:
            raise ProfileNotFoundError(f"프로필을 찾을 수 없습니다: {query.slug}")

        # 후보 = 같은 카테고리의 승인·주문 수신 중 프로필(목록과 같은 조건 — 골라도 못 사면 헛수고)
        pool = await self._repository.list_by_status(
            status=ProfileStatus.APPROVED,
            category=target.primary_category,
            limit=_CANDIDATE_POOL,
            offset=0,
        )
        candidates = [p for p in pool if p.id != target.id]
        if not candidates:
            return []

        # 가격·플랫폼을 타깃 포함 한 번에 읽어 순위 재료를 만든다(N+1 회피)
        all_ids = [target.id] + [p.id for p in candidates]
        prices = await self._packages.min_prices_by_profile_ids(all_ids)
        platforms = await self._packages.platforms_by_profile_ids(all_ids)

        ranked_ids = rank_similar(
            target_price=prices.get(target.id),
            target_platforms=frozenset(platforms.get(target.id, set())),
            candidates=[
                SimilarityCandidate(
                    profile_id=p.id,
                    min_price=prices.get(p.id),
                    platforms=frozenset(platforms.get(p.id, set())),
                )
                for p in candidates
            ],
            limit=query.limit,
        )
        by_id = {p.id: p for p in candidates}
        ordered = [by_id[profile_id] for profile_id in ranked_ids]

        # 카드 보강 — 목록·인기 섹션과 같은 형태(ProfileListingItem 공유)
        covers = await self._portfolio.first_file_names_by_profile_ids(ranked_ids)
        ratings = await self._ratings.get_rating_summaries(
            [p.user_id for p in ordered if p.user_id is not None]
        )

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
