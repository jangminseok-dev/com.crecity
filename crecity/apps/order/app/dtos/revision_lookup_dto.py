from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RevisionListQuery:

    order_id: int
    requester_user_id: int


@dataclass(frozen=True)
class RevisionRequestResult:
    """수정 요청 이력 1건(갭 #84) — 어느 검토 단계에서 어떤 피드백이 나왔는지."""

    id: int
    requested_in: str  # OrderStatus 값(DRAFT_REVIEW=초안, IN_REVIEW=최종)
    comment: str
    created_at: datetime | None
