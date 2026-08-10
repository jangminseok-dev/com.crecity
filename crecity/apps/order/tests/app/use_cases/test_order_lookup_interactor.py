from datetime import datetime, timezone

import pytest

from order.app.dtos.order_lookup_dto import MyOrdersQuery, OrderDetailQuery
from order.app.exceptions import NotOrderParticipantError, OrderNotFoundError
from order.app.use_cases.order_lookup_interactor import OrderLookupInteractor
from order.domain.entities.order_entity import Order, OrderStatus

_NOW = datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc)
BRAND, CREATOR = 100, 200


def _order(id=1):
    return Order(
        id=id,
        package_id=10,
        package_title="릴스 1개",
        brand_user_id=BRAND,
        creator_user_id=CREATOR,
        amount_krw=300000,
        brand_fee_percent=10,
        creator_fee_percent=10,
        requirements="60초 릴스",
        status=OrderStatus.PENDING_ACCEPT,
        deadline_at=_NOW,
    )


class _StubOrderRepository:
    def __init__(self, orders: list[Order]):
        self.orders = orders

    async def create(self, order, entries):
        raise NotImplementedError

    async def find_by_id(self, order_id):
        return next((o for o in self.orders if o.id == order_id), None)

    async def save_transition(self, order, entries):
        raise NotImplementedError

    async def list_by_participant(self, user_id):
        return [o for o in self.orders if user_id in (o.brand_user_id, o.creator_user_id)]

    async def find_expired(self, now, limit):
        raise NotImplementedError


async def test_내가_참여한_주문만_보인다():
    interactor = OrderLookupInteractor(_StubOrderRepository([_order()]))
    assert len(await interactor.list_my_orders(MyOrdersQuery(user_id=BRAND))) == 1
    assert len(await interactor.list_my_orders(MyOrdersQuery(user_id=CREATOR))) == 1
    assert await interactor.list_my_orders(MyOrdersQuery(user_id=999)) == []


async def test_당사자는_상세를_볼_수_있다():
    interactor = OrderLookupInteractor(_StubOrderRepository([_order()]))
    result = await interactor.get_order(OrderDetailQuery(order_id=1, requester_user_id=CREATOR))
    assert result.id == 1
    assert result.brand_total_krw == 330000


async def test_제3자_상세_조회는_NotOrderParticipantError():
    interactor = OrderLookupInteractor(_StubOrderRepository([_order()]))
    with pytest.raises(NotOrderParticipantError):
        await interactor.get_order(OrderDetailQuery(order_id=1, requester_user_id=999))


async def test_없는_주문이면_OrderNotFoundError():
    interactor = OrderLookupInteractor(_StubOrderRepository([]))
    with pytest.raises(OrderNotFoundError):
        await interactor.get_order(OrderDetailQuery(order_id=99, requester_user_id=BRAND))
