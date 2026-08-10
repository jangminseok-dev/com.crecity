from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Notification:
    """인앱 알림 — Outbox 이벤트를 사람이 읽을 문장으로 변환한 결과."""

    id: int
    user_id: int
    event_type: str
    body: str
    link: str | None  # 클릭 시 이동할 앱 내 경로
    is_read: bool
    created_at: datetime | None = None
