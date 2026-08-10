from dataclasses import dataclass


@dataclass(frozen=True)
class OutboxRecord:
    """워커가 읽는 미발행 이벤트(허브 outbox 행)."""

    id: int
    event_type: str
    payload: dict


@dataclass(frozen=True)
class NotificationDraft:
    """이벤트에서 변환된 알림 초안 — publish에서 발행 마킹과 단일 커밋으로 저장된다."""

    user_id: int
    event_type: str
    body: str
    link: str | None


@dataclass(frozen=True)
class RelayResult:

    consumed_events: int
    created_notifications: int
