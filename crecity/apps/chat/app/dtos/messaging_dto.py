from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SendMessageCommand:

    conversation_id: int
    sender_user_id: int
    body: str


@dataclass(frozen=True)
class MessagesQuery:

    conversation_id: int
    requester_user_id: int  # 참여자만


@dataclass(frozen=True)
class MessageResult:

    id: int
    conversation_id: int
    sender_user_id: int
    body: str
    is_mine: bool  # 요청자 기준
    created_at: datetime | None
    image_file_name: str | None = None  # 사진 메시지 — URL 변환은 라우터 몫
