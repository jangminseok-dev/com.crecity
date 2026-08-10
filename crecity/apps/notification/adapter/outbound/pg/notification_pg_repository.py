from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from notification.adapter.outbound.mappers.notification_mapper import NotificationMapper
from notification.adapter.outbound.orm.notification_orm import NotificationOrm
from notification.app.ports.output.notification_repository import NotificationRepository
from notification.domain.entities.notification_entity import Notification


class NotificationPgRepository(NotificationRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_user(self, user_id: int, limit: int) -> list[Notification]:
        result = await self._session.execute(
            select(NotificationOrm)
            .where(NotificationOrm.user_id == user_id)
            .order_by(NotificationOrm.created_at.desc(), NotificationOrm.id.desc())
            .limit(limit)
        )
        return [NotificationMapper.to_entity(orm) for orm in result.scalars()]

    async def unread_count(self, user_id: int) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(NotificationOrm)
            .where(NotificationOrm.user_id == user_id, NotificationOrm.is_read.is_(False))
        )
        return int(result.scalar_one())

    async def mark_all_read(self, user_id: int) -> None:
        await self._session.execute(
            update(NotificationOrm)
            .where(NotificationOrm.user_id == user_id, NotificationOrm.is_read.is_(False))
            .values(is_read=True)
        )
        await self._session.commit()
