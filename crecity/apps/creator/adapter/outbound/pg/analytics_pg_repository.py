from __future__ import annotations

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from creator.adapter.outbound.orm.profile_analytics_orm import ProfileAnalyticsOrm
from creator.app.ports.output.analytics_repository import AnalyticsRepository
from creator.domain.entities.profile_analytics_entity import ProfileAnalytics


def _to_entity(orm: ProfileAnalyticsOrm) -> ProfileAnalytics:
    return ProfileAnalytics(
        id=orm.id,
        profile_id=orm.profile_id,
        platform=orm.platform,
        followers_count=orm.followers_count,
        engagement_permille=orm.engagement_permille,
        screenshot_file_name=orm.screenshot_file_name,
        updated_at=orm.updated_at,
    )


class AnalyticsPgRepository(AnalyticsRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        profile_id: int,
        platform: str,
        followers_count: int,
        engagement_permille: int | None,
        screenshot_file_name: str,
    ) -> ProfileAnalytics:
        updated = await self._session.execute(
            update(ProfileAnalyticsOrm)
            .where(
                ProfileAnalyticsOrm.profile_id == profile_id,
                ProfileAnalyticsOrm.platform == platform,
            )
            .values(
                followers_count=followers_count,
                engagement_permille=engagement_permille,
                screenshot_file_name=screenshot_file_name,
            )
            .returning(ProfileAnalyticsOrm)
        )
        orm = updated.scalar_one_or_none()
        if orm is None:
            created = await self._session.execute(
                insert(ProfileAnalyticsOrm)
                .values(
                    profile_id=profile_id,
                    platform=platform,
                    followers_count=followers_count,
                    engagement_permille=engagement_permille,
                    screenshot_file_name=screenshot_file_name,
                )
                .returning(ProfileAnalyticsOrm)
            )
            orm = created.scalar_one()
        await self._session.commit()
        return _to_entity(orm)

    async def list_by_profile_id(self, profile_id: int) -> list[ProfileAnalytics]:
        result = await self._session.execute(
            select(ProfileAnalyticsOrm)
            .where(ProfileAnalyticsOrm.profile_id == profile_id)
            .order_by(ProfileAnalyticsOrm.followers_count.desc())
        )
        return [_to_entity(orm) for orm in result.scalars()]

    async def delete(self, profile_id: int, platform: str) -> bool:
        result = await self._session.execute(
            delete(ProfileAnalyticsOrm).where(
                ProfileAnalyticsOrm.profile_id == profile_id,
                ProfileAnalyticsOrm.platform == platform,
            )
        )
        await self._session.commit()
        return result.rowcount > 0

    async def followers_total(self, profile_id: int) -> int:
        result = await self._session.execute(
            select(func.coalesce(func.sum(ProfileAnalyticsOrm.followers_count), 0)).where(
                ProfileAnalyticsOrm.profile_id == profile_id
            )
        )
        return int(result.scalar_one())
