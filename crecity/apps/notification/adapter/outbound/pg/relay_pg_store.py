from sqlalchemy.ext.asyncio import AsyncSession

from hub.adapter.outbound.pg.outbox_pg_store import fetch_unpublished, mark_published
from notification.adapter.outbound.orm.notification_orm import NotificationOrm
from notification.app.dtos.outbox_relay_dto import NotificationDraft, OutboxRecord
from notification.app.ports.output.relay_store import RelayStore


class RelayPgStore(RelayStore):
    """허브 outbox 소비 + 알림 생성을 한 세션에서 처리한다."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def fetch_unpublished(self, limit: int) -> list[OutboxRecord]:
        rows = await fetch_unpublished(self._session, limit)
        return [OutboxRecord(id=row.id, event_type=row.event_type, payload=row.payload) for row in rows]

    async def publish(self, event_ids: list[int], drafts: list[NotificationDraft]) -> None:
        for draft in drafts:
            self._session.add(
                NotificationOrm(
                    user_id=draft.user_id,
                    event_type=draft.event_type,
                    body=draft.body[:300],
                    link=draft.link,
                )
            )
        await mark_published(self._session, event_ids)
        await self._session.commit()  # 알림 + 발행 마킹 = 단일 커밋
