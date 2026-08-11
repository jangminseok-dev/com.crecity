from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from admin.adapter.outbound.pg.audit_log_pg_repository import AuditLogPgRepository
from admin.adapter.outbound.pg.audit_record_adapters import PgAuditRecordAdapter
from admin.app.ports.input.profile_review_use_case import ProfileReviewUseCase
from admin.app.use_cases.profile_review_interactor import ProfileReviewInteractor
from core.database import get_db
from hub.dependencies.profile_review_provider import get_profile_review_port


def get_profile_review_use_case(
    db: AsyncSession = Depends(get_db),
) -> ProfileReviewUseCase:
    return ProfileReviewInteractor(
        profiles=get_profile_review_port(),
        record=PgAuditRecordAdapter(AuditLogPgRepository(session=db)),
    )
