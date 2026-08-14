from sqlalchemy import func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from review.adapter.outbound.mappers.review_mapper import ReviewMapper
from review.adapter.outbound.orm.review_orm import ReviewOrm
from review.app.ports.output.review_repository import ReviewRepository
from review.domain.entities.review_entity import Review


class ReviewPgRepository(ReviewRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        order_id: int,
        brand_user_id: int,
        creator_user_id: int,
        communication_score: int,
        timeliness_score: int,
        satisfaction_score: int,
        comment: str,
    ) -> Review:
        result = await self._session.execute(
            insert(ReviewOrm)
            .values(
                order_id=order_id,
                brand_user_id=brand_user_id,
                creator_user_id=creator_user_id,
                communication_score=communication_score,
                timeliness_score=timeliness_score,
                satisfaction_score=satisfaction_score,
                comment=comment,
            )
            .returning(ReviewOrm)
        )
        await self._session.commit()
        return ReviewMapper.to_entity(result.scalar_one())

    async def find_by_id(self, review_id: int) -> Review | None:
        result = await self._session.execute(select(ReviewOrm).where(ReviewOrm.id == review_id))
        orm = result.scalar_one_or_none()
        return ReviewMapper.to_entity(orm) if orm is not None else None

    async def save_reply(self, review_id: int, reply: str) -> Review | None:
        result = await self._session.execute(
            update(ReviewOrm)
            .where(ReviewOrm.id == review_id)
            .values(reply=reply, replied_at=func.now())
            .returning(ReviewOrm)
        )
        orm = result.scalar_one_or_none()
        await self._session.commit()
        return ReviewMapper.to_entity(orm) if orm is not None else None

    async def find_by_order_id(self, order_id: int) -> Review | None:
        result = await self._session.execute(
            select(ReviewOrm).where(ReviewOrm.order_id == order_id)
        )
        orm = result.scalar_one_or_none()
        return ReviewMapper.to_entity(orm) if orm is not None else None

    async def list_by_creator(self, creator_user_id: int) -> list[Review]:
        result = await self._session.execute(
            select(ReviewOrm)
            .where(ReviewOrm.creator_user_id == creator_user_id)
            .order_by(ReviewOrm.created_at.desc(), ReviewOrm.id.desc())
        )
        return [ReviewMapper.to_entity(orm) for orm in result.scalars()]
