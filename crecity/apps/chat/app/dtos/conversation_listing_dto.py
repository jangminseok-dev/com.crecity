from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ConversationResult:

    id: int
    counterpart_name: str  # 보는 사람 기준 상대 이름(허브로 실시간 해석)
    counterpart_slug: str | None  # 상대가 크리에이터면 프로필 슬러그
    last_message: str | None
    last_message_at: datetime | None
    unread_count: int  # 내가 아직 안 읽은 상대 메시지 수(갭 #35)
    created_at: datetime | None
