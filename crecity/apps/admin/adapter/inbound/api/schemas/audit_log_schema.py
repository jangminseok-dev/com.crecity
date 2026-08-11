from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from admin.app.dtos.audit_log_dto import AuditLogResult


class AuditLogResponseSchema(BaseModel):

    id: int
    subject: str  # profile_review | withdrawal_settlement | steward
    note: str
    created_at: datetime | None

    @classmethod
    def from_result(cls, result: AuditLogResult) -> AuditLogResponseSchema:
        return cls(
            id=result.id,
            subject=result.subject,
            note=result.note,
            created_at=result.created_at,
        )
