from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from creator.adapter.outbound.orm.profile_view_orm import ProfileViewDailyOrm
from creator.app.dtos.profile_view_dto import DailyView
from creator.app.ports.output.profile_view_repository import ProfileViewRepository


class ProfileViewPgRepository(ProfileViewRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def increment(self, profile_id: int) -> None:
        today = date.today()
        # UPSERT — 같은 날 동시 조회가 겹쳐도 증가분이 유실되지 않는다
        statement = (
            pg_insert(ProfileViewDailyOrm)
            .values(profile_id=profile_id, view_date=today, view_count=1)
            .on_conflict_do_update(
                constraint="uq_profile_view_day",
                set_={"view_count": ProfileViewDailyOrm.view_count + 1},
            )
        )
        await self._session.execute(statement)
        await self._session.commit()

    async def list_recent(self, profile_id: int, days: int) -> list[DailyView]:
        since = date.today() - timedelta(days=days - 1)
        result = await self._session.execute(
            select(ProfileViewDailyOrm.view_date, ProfileViewDailyOrm.view_count)
            .where(
                ProfileViewDailyOrm.profile_id == profile_id,
                ProfileViewDailyOrm.view_date >= since,
            )
            .order_by(ProfileViewDailyOrm.view_date.asc())
        )
        return [DailyView(view_date=row[0], view_count=int(row[1])) for row in result.all()]
