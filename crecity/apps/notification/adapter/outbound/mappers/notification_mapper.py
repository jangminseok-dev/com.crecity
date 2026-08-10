from notification.adapter.outbound.orm.notification_orm import NotificationOrm
from notification.domain.entities.notification_entity import Notification


class NotificationMapper:
    """NotificationOrm(영속성) ↔ Notification(도메인) 변환을 담당한다."""

    @staticmethod
    def to_entity(orm: NotificationOrm) -> Notification:
        return Notification(
            id=orm.id,
            user_id=orm.user_id,
            event_type=orm.event_type,
            body=orm.body,
            link=orm.link,
            is_read=orm.is_read,
            created_at=orm.created_at,
        )
