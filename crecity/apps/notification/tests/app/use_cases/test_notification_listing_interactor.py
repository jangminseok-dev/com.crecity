from notification.app.use_cases.notification_listing_interactor import (
    NotificationListingInteractor,
)
from notification.domain.entities.notification_entity import Notification


class _StubNotificationRepository:
    def __init__(self, notifications):
        self.notifications = notifications
        self.read_calls = []

    async def list_by_user(self, user_id, limit):
        return [n for n in self.notifications if n.user_id == user_id][:limit]

    async def unread_count(self, user_id):
        return sum(1 for n in self.notifications if n.user_id == user_id and not n.is_read)

    async def mark_all_read(self, user_id):
        self.read_calls.append(user_id)


def _notification(id=1, user_id=200, is_read=False):
    return Notification(
        id=id, user_id=user_id, event_type="order.placed",
        body="새 주문이 도착했습니다", link="/dashboard/orders/1", is_read=is_read,
    )


async def test_내_알림과_안읽음_개수를_돌려준다():
    repo = _StubNotificationRepository([
        _notification(id=1), _notification(id=2, is_read=True), _notification(id=3, user_id=999),
    ])
    result = await NotificationListingInteractor(repo).list_mine(200)
    assert len(result.items) == 2  # 남의 알림 제외
    assert result.unread_count == 1


async def test_모두_읽음_처리를_위임한다():
    repo = _StubNotificationRepository([])
    await NotificationListingInteractor(repo).mark_all_read(200)
    assert repo.read_calls == [200]
