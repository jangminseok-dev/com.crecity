from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from admin.adapter.outbound.pg.audit_log_pg_repository import AuditLogPgRepository
from admin.adapter.outbound.pg.audit_record_adapters import PgAuditRecordAdapter
from admin.adapter.outbound.pg.report_pg_repository import ReportPgRepository
from admin.app.ports.input.report_review_use_case import ReportReviewUseCase
from admin.app.ports.input.report_submission_use_case import ReportSubmissionUseCase
from admin.app.use_cases.report_review_interactor import ReportReviewInteractor
from admin.app.use_cases.report_submission_interactor import ReportSubmissionInteractor
from core.database import get_db


def get_report_submission_use_case(
    db: AsyncSession = Depends(get_db),
) -> ReportSubmissionUseCase:
    return ReportSubmissionInteractor(reports=ReportPgRepository(session=db))


def get_report_review_use_case(db: AsyncSession = Depends(get_db)) -> ReportReviewUseCase:
    return ReportReviewInteractor(
        reports=ReportPgRepository(session=db),
        record=PgAuditRecordAdapter(repository=AuditLogPgRepository(session=db)),
    )
