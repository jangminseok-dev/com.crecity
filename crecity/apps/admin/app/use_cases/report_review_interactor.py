from __future__ import annotations

from admin.app.dtos.report_dto import ReportResolveCommand, ReportResult
from admin.app.exceptions import ReportTargetNotFoundError
from admin.domain.entities.report_entity import ReportStatus
from admin.app.ports.input.report_review_use_case import ReportReviewUseCase
from admin.app.ports.output.report_repository import ReportRepository
from admin.app.ports.output.report_record_port import ReportRecordPort
from admin.app.use_cases.report_submission_interactor import to_result

_LIST_LIMIT = 100


class ReportReviewInteractor(ReportReviewUseCase):

    def __init__(self, reports: ReportRepository, record: ReportRecordPort) -> None:
        self._reports = reports
        self._record = record

    async def list_reports(self, resolved: bool = False) -> list[ReportResult]:
        status = ReportStatus.RESOLVED if resolved else ReportStatus.OPEN
        reports = await self._reports.list_by_status(status, _LIST_LIMIT)
        return [to_result(report) for report in reports]

    async def resolve(self, command: ReportResolveCommand) -> ReportResult:
        report = await self._reports.find_by_id(command.report_id)
        if report is None:
            raise ReportTargetNotFoundError(f"신고를 찾을 수 없습니다: {command.report_id}")
        report.ensure_can_resolve()

        resolved = await self._reports.resolve(
            report_id=command.report_id,
            resolver_user_id=command.resolver_user_id,
            note=command.note.strip(),
        )
        if resolved is None:
            raise ReportTargetNotFoundError(f"신고를 찾을 수 없습니다: {command.report_id}")
        await self._record.record(
            "report_review",
            f"신고 #{resolved.id}({resolved.target_type.value} {resolved.target_id}) 처리 "
            f"— 운영자 {command.resolver_user_id}",
        )
        return to_result(resolved)
