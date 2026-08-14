from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ReviewReplyCommand:

    review_id: int
    requester_user_id: int  # 리뷰를 받은 크리에이터 본인만
    reply: str


@dataclass(frozen=True)
class ReviewReplyResult:

    review_id: int
    reply: str
    replied_at: datetime | None
