from datetime import datetime, timedelta, timezone

import pytest

from order.app.dtos.order_progress_dto import OrderTransitionCommand
from order.app.exceptions import OrderNotFoundError
from order.app.use_cases.order_progress_interactor import OrderProgressInteractor
from order.domain.entities.ledger_entry_entity import LedgerEntryType
from order.domain.entities.order_entity import Order, OrderStatus

_NOW = datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc)
BRAND, CREATOR = 100, 200


class _StubOrderRepository:
    def __init__(self, order: Order | None):
        self.order = order
        self.saved = []  # (order, entries)

    async def create(self, order, entries, events):
        raise NotImplementedError

    async def find_by_id(self, order_id):
        return self.order if self.order and self.order.id == order_id else None

    async def save_transition(self, order, entries, events):
        self.saved.append((order, entries, events))

    async def list_by_participant(self, user_id):
        raise NotImplementedError

    async def find_expired(self, now, limit):
        raise NotImplementedError


def _order(status=OrderStatus.PENDING_ACCEPT, deadline_at=_NOW + timedelta(hours=72)):
    return Order(
        id=1,
        package_id=10,
        package_title="릴스 1개",
        brand_user_id=BRAND,
        creator_user_id=CREATOR,
        amount_krw=300000,
        brand_fee_percent=10,
        creator_fee_percent=10,
        requirements="60초 릴스",
        status=status,
        deadline_at=deadline_at,
    )


def _interactor(order):
    repo = _StubOrderRepository(order)
    return OrderProgressInteractor(orders=repo, review_deadline=timedelta(hours=72)), repo


async def test_수락하면_작업중으로_저장된다():
    interactor, repo = _interactor(_order())
    result = await interactor.accept(OrderTransitionCommand(order_id=1, actor_user_id=CREATOR))
    assert result.status == OrderStatus.IN_PROGRESS.value
    saved_order, saved_entries, saved_events = repo.saved[0]
    assert saved_order.status is OrderStatus.IN_PROGRESS
    assert saved_entries == []
    assert saved_events[0].event_type == "order.accepted"


async def test_거절하면_환불_기입과_함께_저장된다():
    interactor, repo = _interactor(_order())
    result = await interactor.reject(OrderTransitionCommand(order_id=1, actor_user_id=CREATOR))
    assert result.status == OrderStatus.REFUNDED.value
    _, entries, _events = repo.saved[0]
    assert entries[0].entry_type is LedgerEntryType.BRAND_CREDIT_REFUND


async def test_제출하면_검토_마감이_걸린다():
    interactor, repo = _interactor(_order(OrderStatus.IN_PROGRESS, deadline_at=None))
    result = await interactor.submit(OrderTransitionCommand(order_id=1, actor_user_id=CREATOR))
    assert result.status == OrderStatus.IN_REVIEW.value
    assert repo.saved[0][0].deadline_at is not None


async def test_승인하면_적립·수수료_기입과_함께_저장된다():
    interactor, repo = _interactor(_order(OrderStatus.IN_REVIEW))
    result = await interactor.approve(OrderTransitionCommand(order_id=1, actor_user_id=BRAND))
    assert result.status == OrderStatus.COMPLETED.value
    _, entries, _events = repo.saved[0]
    assert {e.entry_type for e in entries} == {
        LedgerEntryType.CREATOR_EARNING,
        LedgerEntryType.PLATFORM_REVENUE,
    }


async def test_없는_주문이면_OrderNotFoundError():
    interactor, _ = _interactor(None)
    with pytest.raises(OrderNotFoundError):
        await interactor.accept(OrderTransitionCommand(order_id=99, actor_user_id=CREATOR))
