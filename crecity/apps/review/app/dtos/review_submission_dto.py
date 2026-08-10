from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ReviewSubmissionCommand:

    order_id: int
    requester_user_id: int  # 주문한 브랜드 본인만
    communication_score: int
    timeliness_score: int
    satisfaction_score: int
    comment: str


@dataclass(frozen=True)
class ReviewResult:

    id: int
    order_id: int
    communication_score: int
    timeliness_score: int
    satisfaction_score: int
    overall_score: float
    comment: str
    created_at: datetime | None
