import pytest

from order.app.dtos.order_adjustment_dto import (
    AdjustmentListQuery,
    DeclineAdjustmentCommand,
    RequestAdjustmentCommand,
)
from order.app.exceptions import (
    AdjustmentNotFoundError,
    DuplicateAdjustmentError,
    NotOrderParticipantError,
    OrderNotFoundError,
)
from order.app.use_cases.order_adjustment_interactor import OrderAdjustmentInteractor
from order.domain.entities.order_adjustment_entity import (
    AdjustmentStatus,
    InvalidAdjustmentError,
    OrderAdjustment,
)
from order.domain.entities.order_entity import (
    InvalidOrderTransitionError,
    NotOrderActorError,
    Order,
    OrderStatus,
)

BRAND, CREATOR = 100, 200


class _StubOrderRepository:
    def __init__(self, order):
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


class _StubAdjustmentRepository:
    def __init__(self):
        self.rows: list[OrderAdjustment] = []
        self.published: list = []  # 함께 적재된 알림 이벤트(갭 #104)

    async def create(self, order_id, extra_amount_krw, reason, events=None):
        self.published += list(events or [])
        row = OrderAdjustment(
            id=len(self.rows) + 1, order_id=order_id, extra_amount_krw=extra_amount_krw,
            reason=reason, status=AdjustmentStatus.REQUESTED,
        )
        self.rows.append(row)
        return row

    async def find_by_id(self, adjustment_id):
        return next((r for r in self.rows if r.id == adjustment_id), None)

    async def list_by_order(self, order_id):
        return [r for r in self.rows if r.order_id == order_id]

    async def has_pending(self, order_id):
        return any(
            r.order_id == order_id and r.status is AdjustmentStatus.REQUESTED for r in self.rows
        )

    async def save_status(self, adjustment_id, status, events=None):
        self.published += list(events or [])
        self.rows = [
            OrderAdjustment(
                id=r.id, order_id=r.order_id, extra_amount_krw=r.extra_amount_krw,
                reason=r.reason, status=status if r.id == adjustment_id else r.status,
            )
            for r in self.rows
        ]

    async def apply_payment(self, adjustment_id, order, entries):
        raise NotImplementedError


def _order(status=OrderStatus.IN_PROGRESS):
    return Order(
        id=1, package_id=10, package_title="릴스 1개", brand_user_id=BRAND,
        creator_user_id=CREATOR, amount_krw=300000, brand_fee_percent=10,
        creator_fee_percent=10, requirements="60초 릴스", status=status, deadline_at=None,
    )


def _interactor(order=None):
    adjustments = _StubAdjustmentRepository()
    interactor = OrderAdjustmentInteractor(
        orders=_StubOrderRepository(order if order is not None else _order()),
        adjustments=adjustments,
    )
    return interactor, adjustments


def _command(actor=CREATOR, extra=100000, reason="촬영 컷 추가 요청분"):
    return RequestAdjustmentCommand(
        order_id=1, actor_user_id=actor, extra_amount_krw=extra, reason=reason
    )


async def test_크리에이터가_추가_금액을_요청하면_대기_상태로_기록된다():
    interactor, adjustments = _interactor()
    result = await interactor.request(_command())
    assert result.extra_amount_krw == 100000
    assert result.status == AdjustmentStatus.REQUESTED.value
    assert len(adjustments.rows) == 1


async def test_브랜드가_요청하면_NotOrderActorError():
    interactor, _ = _interactor()
    with pytest.raises(NotOrderActorError):
        await interactor.request(_command(actor=BRAND))


async def test_진행_중이_아니면_요청할_수_없다():
    interactor, _ = _interactor(_order(OrderStatus.COMPLETED))
    with pytest.raises(InvalidOrderTransitionError):
        await interactor.request(_command())


async def test_대기_중_요청이_있으면_중복_요청은_거부된다():
    interactor, _ = _interactor()
    await interactor.request(_command())
    with pytest.raises(DuplicateAdjustmentError):
        await interactor.request(_command())


async def test_금액이나_사유가_비면_ValueError():
    interactor, _ = _interactor()
    with pytest.raises(ValueError):
        await interactor.request(_command(extra=0))
    with pytest.raises(ValueError):
        await interactor.request(_command(reason="  "))


async def test_브랜드가_거절하면_DECLINED가_되고_재거절은_409():
    interactor, _ = _interactor()
    created = await interactor.request(_command())
    declined = await interactor.decline(
        DeclineAdjustmentCommand(adjustment_id=created.id, actor_user_id=BRAND)
    )
    assert declined.status == AdjustmentStatus.DECLINED.value
    with pytest.raises(InvalidAdjustmentError):
        await interactor.decline(
            DeclineAdjustmentCommand(adjustment_id=created.id, actor_user_id=BRAND)
        )


async def test_크리에이터는_거절할_수_없다():
    interactor, _ = _interactor()
    created = await interactor.request(_command())
    with pytest.raises(NotOrderActorError):
        await interactor.decline(
            DeclineAdjustmentCommand(adjustment_id=created.id, actor_user_id=CREATOR)
        )


async def test_없는_요청_거절은_404():
    interactor, _ = _interactor()
    with pytest.raises(AdjustmentNotFoundError):
        await interactor.decline(
            DeclineAdjustmentCommand(adjustment_id=99, actor_user_id=BRAND)
        )


async def test_목록은_당사자만_볼_수_있다():
    interactor, _ = _interactor()
    await interactor.request(_command())
    assert len(await interactor.list_by_order(AdjustmentListQuery(1, BRAND))) == 1
    with pytest.raises(NotOrderParticipantError):
        await interactor.list_by_order(AdjustmentListQuery(1, 999))


async def test_없는_주문이면_OrderNotFoundError():
    interactor, _ = _interactor()
    with pytest.raises(OrderNotFoundError):
        await interactor.request(
            RequestAdjustmentCommand(
                order_id=99, actor_user_id=CREATOR, extra_amount_krw=1000, reason="사유"
            )
        )


async def test_요청과_거절에_알림_이벤트가_함께_실린다():
    """갭 #104 — 기능은 있는데 상대가 모르면 결제도 거절도 일어나지 않는다."""
    interactor, adjustments = _interactor()
    await interactor.request(_command())
    requested = adjustments.published[-1]
    assert requested.event_type == "order.adjustment_requested"
    assert requested.payload["extra_amount_krw"] == 100000
    assert requested.payload["brand_user_id"] == BRAND

    await interactor.decline(DeclineAdjustmentCommand(adjustment_id=1, actor_user_id=BRAND))
    declined = adjustments.published[-1]
    assert declined.event_type == "order.adjustment_declined"
    assert declined.payload["creator_user_id"] == CREATOR
