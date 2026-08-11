from __future__ import annotations

from sqlalchemy import func, select

from core.database import session_scope
from hub.app.dtos.creator_rating_dto import CreatorRatingSummary
from hub.app.ports.output.creator_rating_port import CreatorRatingPort
from review.adapter.outbound.orm.review_orm import ReviewOrm


class ReviewCreatorRatingGateway(CreatorRatingPort):
    """허브 CreatorRatingPort 계약의 review 구현 — main.py가 조립한다.

    호출자(creator 목록) 트랜잭션과 무관한 읽기 전용 조회라 자체 세션을 연다.
    overall = 3축 평균 — review_listing_interactor의 집계 의미와 동일.
    """

    async def get_rating_summaries(
        self, creator_user_ids: list[int]
    ) -> dict[int, CreatorRatingSummary]:
        if not creator_user_ids:
            return {}
        async with session_scope() as session:
            result = await session.execute(
                select(
                    ReviewOrm.creator_user_id,
                    func.avg(
                        (
                            ReviewOrm.communication_score
                            + ReviewOrm.timeliness_score
                            + ReviewOrm.satisfaction_score
                        )
                        / 3.0
                    ),
                    func.count(),
                )
                .where(ReviewOrm.creator_user_id.in_(creator_user_ids))
                .group_by(ReviewOrm.creator_user_id)
            )
            return {
                creator_user_id: CreatorRatingSummary(
                    creator_user_id=creator_user_id,
                    average_overall=round(float(average), 1),
                    review_count=int(count),
                )
                for creator_user_id, average, count in result
            }
