from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AuditLogResult:

    id: int
    subject: str
    note: str
    created_at: datetime | None
