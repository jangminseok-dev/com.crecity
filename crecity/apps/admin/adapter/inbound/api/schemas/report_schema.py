from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from admin.app.dtos.report_dto import ReportResult
from admin.domain.entities.report_entity import REASON_MAX_LENGTH, ReportTargetType


class ReportSubmissionRequestSchema(BaseModel):

    target_type: ReportTargetType
    target_id: int = Field(ge=1)
    reason: str = Field(max_length=REASON_MAX_LENGTH)


class ReportResolveRequestSchema(BaseModel):

    note: str = Field(default="", max_length=2000)


class ReportResponseSchema(BaseModel):

    id: int
    reporter_user_id: int
    target_type: str
    target_id: int
    reason: str
    status: str
    resolution_note: str
    created_at: datetime | None
    resolved_at: datetime | None

    @classmethod
    def from_result(cls, result: ReportResult) -> ReportResponseSchema:
        return cls(
            id=result.id,
            reporter_user_id=result.reporter_user_id,
            target_type=result.target_type,
            target_id=result.target_id,
            reason=result.reason,
            status=result.status,
            resolution_note=result.resolution_note,
            created_at=result.created_at,
            resolved_at=result.resolved_at,
        )
