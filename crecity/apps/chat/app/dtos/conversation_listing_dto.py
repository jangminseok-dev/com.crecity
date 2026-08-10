from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ConversationResult:

    id: int
    counterpart_name: str  # 보는 사람 기준 상대 이름(허브로 실시간 해석)
    counterpart_slug: str | None  # 상대가 크리에이터면 프로필 슬러그
    last_message: str | None
    last_message_at: datetime | None
    created_at: datetime | None
