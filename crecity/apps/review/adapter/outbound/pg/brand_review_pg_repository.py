from __future__ import annotations

from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from hub.adapter.outbound.pg.outbox_pg_store import enqueue_events
from hub.app.dtos.outbox_event_dto import OutboxEvent
from review.adapter.outbound.orm.brand_review_orm import BrandReviewOrm
from review.app.dtos.brand_review_dto import BrandRatingResult, BrandReviewResult
from review.app.ports.output.brand_review_repository import BrandReviewRepository


def _to_result(orm: BrandReviewOrm) -> BrandReviewResult:
    return BrandReviewResult(
        id=orm.id,
        order_id=orm.order_id,
        score=orm.score,
        comment=orm.comment,
        created_at=orm.created_at,
    )


class BrandReviewPgRepository(BrandReviewRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        order_id: int,
        brand_user_id: int,
        creator_user_id: int,
        score: int,
        comment: str,
        events: list[OutboxEvent] | None = None,
    ) -> BrandReviewResult:
        result = await self._session.execute(
            insert(BrandReviewOrm)
            .values(
                order_id=order_id,
                brand_user_id=brand_user_id,
                creator_user_id=creator_user_id,
                score=score,
                comment=comment,
            )
            .returning(BrandReviewOrm)
        )
        orm = result.scalar_one()
        enqueue_events(self._session, events or [])  # 저장과 단일 커밋(BOUNDARIES §1)
        await self._session.commit()
        return _to_result(orm)

    async def find_by_order_id(self, order_id: int) -> BrandReviewResult | None:
        result = await self._session.execute(
            select(BrandReviewOrm).where(BrandReviewOrm.order_id == order_id)
        )
        orm = result.scalar_one_or_none()
        return _to_result(orm) if orm is not None else None

    async def get_brand_rating(self, brand_user_id: int) -> BrandRatingResult:
        row = (
            await self._session.execute(
                select(func.avg(BrandReviewOrm.score), func.count()).where(
                    BrandReviewOrm.brand_user_id == brand_user_id
                )
            )
        ).one()
        return BrandRatingResult(
            average_score=round(float(row[0]), 1) if row[0] is not None else None,
            total=int(row[1]),
        )
