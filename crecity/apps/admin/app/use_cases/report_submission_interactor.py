from __future__ import annotations

from admin.app.dtos.report_dto import ReportResult, ReportSubmissionCommand
from admin.app.exceptions import DuplicateReportError
from admin.app.ports.input.report_submission_use_case import ReportSubmissionUseCase
from admin.app.ports.output.report_repository import ReportRepository
from admin.domain.entities.report_entity import Report, ReportTargetType, validate_reason


def to_result(report: Report) -> ReportResult:
    return ReportResult(
        id=report.id,
        reporter_user_id=report.reporter_user_id,
        target_type=report.target_type.value,
        target_id=report.target_id,
        reason=report.reason,
        status=report.status.value,
        resolution_note=report.resolution_note,
        created_at=report.created_at,
        resolved_at=report.resolved_at,
    )


class ReportSubmissionInteractor(ReportSubmissionUseCase):

    def __init__(self, reports: ReportRepository) -> None:
        self._reports = reports

    async def submit(self, command: ReportSubmissionCommand) -> ReportResult:
        target_type = ReportTargetType(command.target_type)
        reason = validate_reason(command.reason)
        # 같은 대상에 대기 중인 신고가 있으면 다시 받지 않는다(중복 큐 방지)
        if await self._reports.exists_open_by_reporter(
            command.reporter_user_id, target_type, command.target_id
        ):
            raise DuplicateReportError("이미 접수해 처리 대기 중인 신고가 있습니다.")

        report = await self._reports.create(
            reporter_user_id=command.reporter_user_id,
            target_type=target_type,
            target_id=command.target_id,
            reason=reason,
        )
        return to_result(report)
