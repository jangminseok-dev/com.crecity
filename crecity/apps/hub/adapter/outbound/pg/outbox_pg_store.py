from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from hub.adapter.outbound.orm.outbox_event_orm import OutboxEventOrm
from hub.app.dtos.outbox_event_dto import OutboxEvent


def enqueue_events(session: AsyncSession, events: list[OutboxEvent]) -> None:
    """이벤트를 호출자 세션에 적재한다 — **커밋하지 않는다**(호출자 트랜잭션과 원자성).

    발행 스포크는 상태 변경 커밋 직전에 호출한다: 상태+원장+이벤트 = 단일 커밋.
    """
    for event in events:
        session.add(OutboxEventOrm(event_type=event.event_type, payload=event.payload))


async def fetch_unpublished(session: AsyncSession, limit: int) -> list[OutboxEventOrm]:
    """미발행 이벤트 — 오래된 순(워커 전용)."""
    result = await session.execute(
        select(OutboxEventOrm)
        .where(OutboxEventOrm.published_at.is_(None))
        .order_by(OutboxEventOrm.id)
        .limit(limit)
    )
    return list(result.scalars())


async def mark_published(session: AsyncSession, event_ids: list[int]) -> None:
    """발행 마킹 — **커밋하지 않는다**(소비 결과와 같은 트랜잭션 — 중복 발송 방지)."""
    if not event_ids:
        return
    await session.execute(
        update(OutboxEventOrm)
        .where(OutboxEventOrm.id.in_(event_ids))
        .values(published_at=datetime.now(timezone.utc))
    )
