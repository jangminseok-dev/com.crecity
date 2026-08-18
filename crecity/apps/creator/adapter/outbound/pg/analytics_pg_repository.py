from __future__ import annotations

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from creator.adapter.outbound.orm.audience_breakdown_orm import AudienceBreakdownOrm
from creator.adapter.outbound.orm.creator_profile_orm import CreatorProfileOrm
from creator.adapter.outbound.orm.profile_analytics_orm import ProfileAnalyticsOrm
from creator.app.ports.output.analytics_repository import AnalyticsRepository
from creator.domain.entities.profile_analytics_entity import ProfileAnalytics
from creator.domain.value_objects.audience_breakdown import AudienceDimension, AudienceShare
from hub.app.dtos.profile_review_dto import FlaggedAnalyticsSummary


def _to_entity(
    orm: ProfileAnalyticsOrm, audience: tuple[AudienceShare, ...] = ()
) -> ProfileAnalytics:
    return ProfileAnalytics(
        id=orm.id,
        profile_id=orm.profile_id,
        platform=orm.platform,
        followers_count=orm.followers_count,
        engagement_permille=orm.engagement_permille,
        screenshot_file_name=orm.screenshot_file_name,
        updated_at=orm.updated_at,
        top_audience_region=orm.top_audience_region,
        audience=audience,
        flag_reason=orm.flag_reason,
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
        top_audience_region: str | None = None,
        audience: list[AudienceShare] | None = None,
        flag_reason: str | None = None,
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
                top_audience_region=top_audience_region,
                flag_reason=flag_reason,
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
                    top_audience_region=top_audience_region,
                    flag_reason=flag_reason,
                )
                .returning(ProfileAnalyticsOrm)
            )
            orm = created.scalar_one()

        # 오디언스 비율은 통째로 교체한다 — 부분 갱신은 합계 검증을 무력화한다
        await self._session.execute(
            delete(AudienceBreakdownOrm).where(AudienceBreakdownOrm.analytics_id == orm.id)
        )
        shares = tuple(audience or ())
        if shares:
            await self._session.execute(
                insert(AudienceBreakdownOrm),
                [
                    {
                        "analytics_id": orm.id,
                        "dimension": share.dimension.value,
                        "bucket": share.bucket,
                        "share_permille": share.share_permille,
                    }
                    for share in shares
                ],
            )
        await self._session.commit()
        return _to_entity(orm, shares)

    async def _audience_by_analytics(
        self, analytics_ids: list[int]
    ) -> dict[int, tuple[AudienceShare, ...]]:
        if not analytics_ids:
            return {}
        rows = await self._session.execute(
            select(AudienceBreakdownOrm).where(
                AudienceBreakdownOrm.analytics_id.in_(analytics_ids)
            )
        )
        grouped: dict[int, list[AudienceShare]] = {}
        for row in rows.scalars():
            grouped.setdefault(row.analytics_id, []).append(
                AudienceShare(
                    dimension=AudienceDimension(row.dimension),
                    bucket=row.bucket,
                    share_permille=row.share_permille,
                )
            )
        return {key: tuple(value) for key, value in grouped.items()}

    async def list_by_profile_id(self, profile_id: int) -> list[ProfileAnalytics]:
        result = await self._session.execute(
            select(ProfileAnalyticsOrm)
            .where(ProfileAnalyticsOrm.profile_id == profile_id)
            .order_by(ProfileAnalyticsOrm.followers_count.desc())
        )
        rows = list(result.scalars())
        audience = await self._audience_by_analytics([orm.id for orm in rows])
        return [_to_entity(orm, audience.get(orm.id, ())) for orm in rows]

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

    # ── 이상치 재검토 큐(갭 #82) — 허브 게이트웨이 전용(포트 미승격) ──────────

    async def list_flagged(self) -> list[FlaggedAnalyticsSummary]:
        result = await self._session.execute(
            select(ProfileAnalyticsOrm, CreatorProfileOrm.slug, CreatorProfileOrm.name)
            .join(CreatorProfileOrm, CreatorProfileOrm.id == ProfileAnalyticsOrm.profile_id)
            .where(ProfileAnalyticsOrm.flag_reason.is_not(None))
            .order_by(ProfileAnalyticsOrm.updated_at)
        )
        return [
            FlaggedAnalyticsSummary(
                id=orm.id,
                profile_slug=slug,
                profile_name=name,
                platform=orm.platform,
                followers_count=orm.followers_count,
                engagement_permille=orm.engagement_permille,
                flag_reason=orm.flag_reason,
                updated_at=orm.updated_at,
            )
            for orm, slug, name in result.all()
        ]

    async def clear_flag(self, analytics_id: int) -> bool:
        result = await self._session.execute(
            update(ProfileAnalyticsOrm)
            .where(ProfileAnalyticsOrm.id == analytics_id)
            .values(flag_reason=None)
        )
        await self._session.commit()
        return result.rowcount > 0
