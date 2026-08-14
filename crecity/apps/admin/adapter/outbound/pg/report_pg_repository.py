from sqlalchemy import exists, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from admin.adapter.outbound.orm.report_orm import AdminReportOrm
from admin.app.ports.output.report_repository import ReportRepository
from admin.domain.entities.report_entity import Report, ReportStatus, ReportTargetType
from sqlalchemy import func


def _to_entity(orm: AdminReportOrm) -> Report:
    return Report(
        id=orm.id,
        reporter_user_id=orm.reporter_user_id,
        target_type=ReportTargetType(orm.target_type),
        target_id=orm.target_id,
        reason=orm.reason,
        status=ReportStatus(orm.status),
        resolution_note=orm.resolution_note,
        resolved_by_user_id=orm.resolved_by_user_id,
        created_at=orm.created_at,
        resolved_at=orm.resolved_at,
    )


class ReportPgRepository(ReportRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        reporter_user_id: int,
        target_type: ReportTargetType,
        target_id: int,
        reason: str,
    ) -> Report:
        result = await self._session.execute(
            insert(AdminReportOrm)
            .values(
                reporter_user_id=reporter_user_id,
                target_type=target_type.value,
                target_id=target_id,
                reason=reason,
                status=ReportStatus.OPEN.value,
            )
            .returning(AdminReportOrm)
        )
        await self._session.commit()
        return _to_entity(result.scalar_one())

    async def find_by_id(self, report_id: int) -> Report | None:
        result = await self._session.execute(
            select(AdminReportOrm).where(AdminReportOrm.id == report_id)
        )
        orm = result.scalar_one_or_none()
        return _to_entity(orm) if orm is not None else None

    async def exists_open_by_reporter(
        self, reporter_user_id: int, target_type: ReportTargetType, target_id: int
    ) -> bool:
        result = await self._session.execute(
            select(
                exists().where(
                    AdminReportOrm.reporter_user_id == reporter_user_id,
                    AdminReportOrm.target_type == target_type.value,
                    AdminReportOrm.target_id == target_id,
                    AdminReportOrm.status == ReportStatus.OPEN.value,
                )
            )
        )
        return bool(result.scalar())

    async def list_by_status(self, status: ReportStatus, limit: int) -> list[Report]:
        statement = select(AdminReportOrm).where(AdminReportOrm.status == status.value)
        # 대기는 오래 기다린 것부터, 처리 완료는 최근 판단부터 보는 게 자연스럽다
        statement = (
            statement.order_by(AdminReportOrm.created_at.asc(), AdminReportOrm.id.asc())
            if status is ReportStatus.OPEN
            else statement.order_by(AdminReportOrm.resolved_at.desc(), AdminReportOrm.id.desc())
        )
        result = await self._session.execute(statement.limit(limit))
        return [_to_entity(orm) for orm in result.scalars()]

    async def resolve(self, report_id: int, resolver_user_id: int, note: str) -> Report | None:
        result = await self._session.execute(
            update(AdminReportOrm)
            .where(AdminReportOrm.id == report_id)
            .values(
                status=ReportStatus.RESOLVED.value,
                resolution_note=note,
                resolved_by_user_id=resolver_user_id,
                resolved_at=func.now(),
            )
            .returning(AdminReportOrm)
        )
        orm = result.scalar_one_or_none()
        await self._session.commit()
        return _to_entity(orm) if orm is not None else None
