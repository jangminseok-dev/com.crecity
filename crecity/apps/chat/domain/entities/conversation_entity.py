from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


class NotParticipantError(Exception):
    """대화 참여자가 아님 — 라우터에서 403으로 변환."""


@dataclass(frozen=True, slots=True)
class Conversation:
    """대화방 — 브랜드↔크리에이터 1:1(쌍당 1개). 주문 전 협상·분쟁 근거 기록(BOUNDARIES)."""

    id: int
    brand_user_id: int
    creator_user_id: int
    created_at: datetime | None = None

    def is_participant(self, user_id: int) -> bool:
        return user_id in (self.brand_user_id, self.creator_user_id)

    def ensure_participant(self, user_id: int) -> None:
        if not self.is_participant(user_id):
            raise NotParticipantError("대화 참여자만 접근할 수 있습니다.")

    def counterpart_of(self, user_id: int) -> int:
        """상대 참여자 — 호출 전 참여자 검증 전제."""
        return self.creator_user_id if user_id == self.brand_user_id else self.brand_user_id


@dataclass(frozen=True, slots=True)
class Message:
    """메시지 — 수정·삭제 없음(분쟁 근거 보존)."""

    id: int
    conversation_id: int
    sender_user_id: int
    body: str
    created_at: datetime | None = None
