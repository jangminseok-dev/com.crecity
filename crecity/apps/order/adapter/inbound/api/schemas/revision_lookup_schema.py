from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from order.app.dtos.revision_lookup_dto import RevisionRequestResult


class RevisionRequestResponseSchema(BaseModel):

    id: int
    requested_in: str  # DRAFT_REVIEW=초안 검토, IN_REVIEW=최종 검토
    comment: str
    created_at: datetime | None

    @classmethod
    def from_result(cls, result: RevisionRequestResult) -> RevisionRequestResponseSchema:
        return cls(
            id=result.id,
            requested_in=result.requested_in,
            comment=result.comment,
            created_at=result.created_at,
        )
