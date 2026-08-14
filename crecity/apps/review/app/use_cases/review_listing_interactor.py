from __future__ import annotations

from hub.app.ports.output.creator_ref_port import CreatorRefPort
from review.app.dtos.review_listing_dto import (
    CreatorReviewsQuery,
    CreatorReviewsResult,
    ReviewListItem,
)
from review.app.exceptions import CreatorNotFoundError
from review.app.ports.input.review_listing_use_case import ReviewListingUseCase
from review.app.ports.output.review_repository import ReviewRepository
from review.domain.entities.review_entity import Review


def _average(values: list[int]) -> float | None:
    return round(sum(values) / len(values), 1) if values else None


class ReviewListingInteractor(ReviewListingUseCase):

    def __init__(self, reviews: ReviewRepository, creators: CreatorRefPort) -> None:
        self._reviews = reviews
        self._creators = creators

    async def list_for_creator(self, query: CreatorReviewsQuery) -> CreatorReviewsResult:
        creator = await self._creators.get_creator_by_slug(query.slug)
        if creator is None:
            raise CreatorNotFoundError(f"크리에이터를 찾을 수 없습니다: {query.slug}")
        reviews = await self._reviews.list_by_creator(creator.creator_user_id)

        def to_item(review: Review) -> ReviewListItem:
            locked = not query.viewer_logged_in  # 블러 정책 — 원문은 로그인 시에만
            return ReviewListItem(
                id=review.id,
                communication_score=review.communication_score,
                timeliness_score=review.timeliness_score,
                satisfaction_score=review.satisfaction_score,
                overall_score=review.overall_score(),
                comment=None if locked else review.comment,
                is_locked=locked,
                created_at=review.created_at,
                reply=None if locked or not review.reply else review.reply,
                replied_at=None if locked else review.replied_at,
                can_reply=(
                    query.viewer_user_id is not None
                    and query.viewer_user_id == review.creator_user_id
                    and not review.reply
                ),
            )

        return CreatorReviewsResult(
            total=len(reviews),
            average_overall=(
                round(sum(r.overall_score() for r in reviews) / len(reviews), 1)
                if reviews
                else None
            ),
            average_communication=_average([r.communication_score for r in reviews]),
            average_timeliness=_average([r.timeliness_score for r in reviews]),
            average_satisfaction=_average([r.satisfaction_score for r in reviews]),
            items=[to_item(review) for review in reviews],
        )
