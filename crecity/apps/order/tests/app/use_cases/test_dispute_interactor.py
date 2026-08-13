from datetime import datetime, timedelta, timezone

import pytest

from order.app.dtos.dispute_dto import DisputeListQuery, RaiseDisputeCommand
from order.app.exceptions import NotOrderParticipantError, OrderNotFoundError
from order.app.use_cases.dispute_interactor import DisputeInteractor
from order.domain.entities.dispute_entity import Dispute, DisputeStatus
from order.domain.entities.order_entity import (
    InvalidOrderTransitionError,
    NotOrderActorError,
    Order,
    OrderStatus,
)

_NOW = datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc)
BRAND, CREATOR = 100, 200
REASON = "제출한 콘텐츠가 요구사항과 전혀 다릅니다 — 재작업도 거부당했습니다."


class _StubOrderRepository:
    def __init__(self, order: Order | None):
        self.order = order

    async def create(self, order, entries, events, credit_spend=None):
        raise NotImplementedError

    async def create_many(self, drafts, credit_spend=None):
        raise NotImplementedError

    async def find_by_id(self, order_id):
        return self.order if self.order and self.order.id == order_id else None

    async def save_transition(self, order, entries, events):
        raise NotImplementedError

    async def list_by_participant(self, user_id):
        raise NotImplementedError

    async def find_expired(self, now, limit):
        raise NotImplementedError


class _StubDisputeRepository:
    def __init__(self):
        self.items: list[Dispute] = []
        self.events: list = []

    async def add(self, order_id, raised_by_user_id, reason, events):
        dispute = Dispute(
            id=len(self.items) + 1,
            order_id=order_id,
            raised_by_user_id=raised_by_user_id,
            reason=reason,
            status=DisputeStatus.OPEN,
            created_at=_NOW,
        )
        self.items.append(dispute)
        self.events.extend(events)
        return dispute

    async def find_by_id(self, dispute_id):
        return next((d for d in self.items if d.id == dispute_id), None)

    async def find_open_by_order(self, order_id):
        return next(
            (d for d in self.items if d.order_id == order_id and d.status is DisputeStatus.OPEN),
            None,
        )

    async def list_by_order(self, order_id):
        return [d for d in self.items if d.order_id == order_id]

    async def list_open(self):
        return [d for d in self.items if d.status is DisputeStatus.OPEN]

    async def resolve(self, dispute, order, entries, events):
        raise NotImplementedError


def _order(status=OrderStatus.IN_REVIEW):
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
        deadline_at=_NOW + timedelta(hours=72),
    )


def _interactor(order):
    disputes = _StubDisputeRepository()
    return DisputeInteractor(orders=_StubOrderRepository(order), disputes=disputes), disputes


async def test_당사자가_신고하면_OPEN으로_기록되고_알림_이벤트가_실린다():
    interactor, disputes = _interactor(_order())
    result = await interactor.raise_dispute(
        RaiseDisputeCommand(order_id=1, actor_user_id=BRAND, reason=REASON)
    )
    assert result.status == DisputeStatus.OPEN.value
    assert result.resolution is None
    assert len(disputes.items) == 1
    assert disputes.events[0].event_type == "order.dispute_raised"


async def test_제3자가_신고하면_NotOrderActorError():
    interactor, disputes = _interactor(_order())
    with pytest.raises(NotOrderActorError):
        await interactor.raise_dispute(
            RaiseDisputeCommand(order_id=1, actor_user_id=999, reason=REASON)
        )
    assert disputes.items == []


async def test_진행_중이_아닌_주문은_신고할_수_없다():
    interactor, _ = _interactor(_order(OrderStatus.COMPLETED))
    with pytest.raises(InvalidOrderTransitionError):
        await interactor.raise_dispute(
            RaiseDisputeCommand(order_id=1, actor_user_id=BRAND, reason=REASON)
        )


async def test_대기_중_분쟁이_있으면_중복_신고할_수_없다():
    interactor, _ = _interactor(_order())
    await interactor.raise_dispute(
        RaiseDisputeCommand(order_id=1, actor_user_id=BRAND, reason=REASON)
    )
    with pytest.raises(InvalidOrderTransitionError):
        await interactor.raise_dispute(
            RaiseDisputeCommand(order_id=1, actor_user_id=CREATOR, reason=REASON)
        )


async def test_사유가_짧으면_ValueError():
    interactor, _ = _interactor(_order())
    with pytest.raises(ValueError):
        await interactor.raise_dispute(
            RaiseDisputeCommand(order_id=1, actor_user_id=BRAND, reason="싫어요")
        )


async def test_목록은_당사자만_조회할_수_있다():
    interactor, _ = _interactor(_order())
    await interactor.raise_dispute(
        RaiseDisputeCommand(order_id=1, actor_user_id=BRAND, reason=REASON)
    )
    results = await interactor.list_disputes(
        DisputeListQuery(order_id=1, requester_user_id=CREATOR)
    )
    assert len(results) == 1
    with pytest.raises(NotOrderParticipantError):
        await interactor.list_disputes(DisputeListQuery(order_id=1, requester_user_id=999))


async def test_없는_주문이면_OrderNotFoundError():
    interactor, _ = _interactor(None)
    with pytest.raises(OrderNotFoundError):
        await interactor.raise_dispute(
            RaiseDisputeCommand(order_id=1, actor_user_id=BRAND, reason=REASON)
        )
