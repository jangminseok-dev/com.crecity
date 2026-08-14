from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ReportSubmissionCommand:

    reporter_user_id: int
    target_type: str  # ReportTargetType 값
    target_id: int
    reason: str


@dataclass(frozen=True)
class ReportResolveCommand:

    report_id: int
    resolver_user_id: int
    note: str


@dataclass(frozen=True)
class ReportResult:

    id: int
    reporter_user_id: int
    target_type: str
    target_id: int
    reason: str
    status: str
    resolution_note: str
    created_at: datetime | None
    resolved_at: datetime | None
