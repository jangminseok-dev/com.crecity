from datetime import datetime, timezone

import pytest

from order.app.dtos.order_cancellation_dto import CancellationCommand
from order.app.exceptions import OrderNotFoundError
from order.app.use_cases.order_cancellation_interactor import OrderCancellationInteractor
from order.domain.entities.ledger_entry_entity import LedgerEntryType
from order.domain.entities.order_entity import InvalidOrderTransitionError, Order, OrderStatus

_NOW = datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)
BRAND, CREATOR = 100, 200


class _StubOrderRepository:
    def __init__(self, order: Order | None):
        self.order = order
        self.saved = []  # (order, entries, events)

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


class _StubDisputeRepository:
    """대기 분쟁 유무만 답한다 — 승인·취소 동의 보류 판단에 쓰는 메서드만."""

    def __init__(self, open_order_ids=()):
        self.open_order_ids = set(open_order_ids)

    async def find_open_by_order(self, order_id):
        return object() if order_id in self.open_order_ids else None


def _order(status=OrderStatus.IN_PROGRESS, cancel_requested_by=None):
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
        deadline_at=None,
        cancel_requested_by=cancel_requested_by,
    )


def _interactor(order, open_dispute=False):
    repo = _StubOrderRepository(order)
    disputes = _StubDisputeRepository([order.id] if open_dispute and order else [])
    return OrderCancellationInteractor(orders=repo, disputes=disputes), repo


async def test_대기_분쟁이_있으면_취소_동의가_보류된다():
    interactor, repo = _interactor(_order(cancel_requested_by=BRAND), open_dispute=True)
    with pytest.raises(InvalidOrderTransitionError, match="분쟁"):
        await interactor.consent(CancellationCommand(order_id=1, actor_user_id=CREATOR))
    assert repo.saved == []


async def test_취소_요청이_저장되고_이벤트에_요청자가_실린다():
    interactor, repo = _interactor(_order())
    result = await interactor.request(CancellationCommand(order_id=1, actor_user_id=BRAND))
    assert result.cancel_requested_by == BRAND
    saved_order, entries, events = repo.saved[0]
    assert saved_order.cancel_requested_by == BRAND
    assert entries == []
    assert events[0].event_type == "order.cancel_requested"
    assert events[0].payload["requested_by"] == BRAND


async def test_동의하면_취소와_환불_기입이_원자적으로_저장된다():
    interactor, repo = _interactor(_order(cancel_requested_by=BRAND))
    result = await interactor.consent(CancellationCommand(order_id=1, actor_user_id=CREATOR))
    assert result.status == OrderStatus.CANCELLED.value
    saved_order, entries, events = repo.saved[0]
    assert saved_order.status is OrderStatus.CANCELLED
    assert entries[0].entry_type is LedgerEntryType.BRAND_CREDIT_REFUND
    assert events[0].event_type == "order.cancelled"


async def test_거부하면_요청이_해제되고_요청자_스냅샷이_이벤트에_실린다():
    interactor, repo = _interactor(_order(cancel_requested_by=CREATOR))
    result = await interactor.decline(CancellationCommand(order_id=1, actor_user_id=BRAND))
    assert result.cancel_requested_by is None
    saved_order, _entries, events = repo.saved[0]
    assert saved_order.cancel_requested_by is None
    assert events[0].event_type == "order.cancel_declined"
    assert events[0].payload["requested_by"] == CREATOR


async def test_없는_주문이면_OrderNotFoundError():
    interactor, _ = _interactor(None)
    with pytest.raises(OrderNotFoundError):
        await interactor.request(CancellationCommand(order_id=99, actor_user_id=BRAND))
