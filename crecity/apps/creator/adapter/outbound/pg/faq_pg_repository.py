from __future__ import annotations

from sqlalchemy import delete, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from creator.adapter.outbound.orm.profile_faq_orm import ProfileFaqOrm
from creator.app.ports.output.faq_repository import FaqRepository
from creator.domain.entities.profile_faq_entity import ProfileFaq


def _to_entity(orm: ProfileFaqOrm) -> ProfileFaq:
    return ProfileFaq(
        id=orm.id,
        profile_id=orm.profile_id,
        question=orm.question,
        answer=orm.answer,
        created_at=orm.created_at,
    )


class FaqPgRepository(FaqRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, profile_id: int, question: str, answer: str) -> ProfileFaq:
        result = await self._session.execute(
            insert(ProfileFaqOrm)
            .values(profile_id=profile_id, question=question, answer=answer)
            .returning(ProfileFaqOrm)
        )
        orm = result.scalar_one()
        await self._session.commit()
        return _to_entity(orm)

    async def list_by_profile_id(self, profile_id: int) -> list[ProfileFaq]:
        result = await self._session.execute(
            select(ProfileFaqOrm)
            .where(ProfileFaqOrm.profile_id == profile_id)
            .order_by(ProfileFaqOrm.created_at, ProfileFaqOrm.id)
        )
        return [_to_entity(orm) for orm in result.scalars()]

    async def count_by_profile_id(self, profile_id: int) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(ProfileFaqOrm)
            .where(ProfileFaqOrm.profile_id == profile_id)
        )
        return int(result.scalar_one())

    async def delete(self, profile_id: int, faq_id: int) -> bool:
        result = await self._session.execute(
            delete(ProfileFaqOrm).where(
                ProfileFaqOrm.id == faq_id, ProfileFaqOrm.profile_id == profile_id
            )
        )
        await self._session.commit()
        return result.rowcount > 0
