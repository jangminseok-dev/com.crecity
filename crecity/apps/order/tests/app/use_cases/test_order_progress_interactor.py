from datetime import datetime, timedelta, timezone

import pytest

from order.app.dtos.order_progress_dto import OrderTransitionCommand, RevisionRequestCommand
from order.app.exceptions import OrderNotFoundError
from order.app.use_cases.order_progress_interactor import OrderProgressInteractor
from order.domain.entities.ledger_entry_entity import LedgerEntryType
from order.domain.entities.order_entity import (
    InvalidOrderTransitionError,
    Order,
    OrderStatus,
)

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

    async def save_transition(self, order, entries, events, revision_comment=None):
        self.saved.append((order, entries, events))
        self.revision_comments = getattr(self, "revision_comments", []) + (
            [revision_comment] if revision_comment is not None else []
        )

    async def list_by_participant(self, user_id):
        raise NotImplementedError

    async def find_expired(self, now, limit):
        raise NotImplementedError


class _StubDeliverableRepository:
    def __init__(self, count: int):
        self.count = count

    async def add(self, order_id, kind, file_name, original_name, url):
        raise NotImplementedError

    async def list_by_order(self, order_id):
        raise NotImplementedError

    async def count_by_order(self, order_id):
        return self.count


class _StubDisputeRepository:
    """대기 분쟁 유무만 답한다 — 승인·취소 동의 보류 판단에 쓰는 메서드만."""

    def __init__(self, open_order_ids=()):
        self.open_order_ids = set(open_order_ids)

    async def find_open_by_order(self, order_id):
        return object() if order_id in self.open_order_ids else None


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


def _interactor(order, deliverable_count=1, open_dispute=False):
    repo = _StubOrderRepository(order)
    interactor = OrderProgressInteractor(
        orders=repo,
        deliverables=_StubDeliverableRepository(deliverable_count),
        disputes=_StubDisputeRepository([order.id] if open_dispute and order else []),
        review_deadline=timedelta(hours=72),
    )
    return interactor, repo


async def test_대기_분쟁이_있으면_승인이_보류된다():
    interactor, repo = _interactor(_order(status=OrderStatus.IN_REVIEW), open_dispute=True)
    with pytest.raises(InvalidOrderTransitionError, match="분쟁"):
        await interactor.approve(OrderTransitionCommand(order_id=1, actor_user_id=BRAND))
    assert repo.saved == []  # 전이·원장 기입 없음


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


async def test_납품물이_없으면_제출할_수_없다():
    interactor, repo = _interactor(
        _order(OrderStatus.IN_PROGRESS, deadline_at=None), deliverable_count=0
    )
    with pytest.raises(InvalidOrderTransitionError):
        await interactor.submit(OrderTransitionCommand(order_id=1, actor_user_id=CREATOR))
    assert repo.saved == []


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


async def test_초안_제출하면_초안_검토와_마감이_저장된다():
    interactor, repo = _interactor(_order(OrderStatus.IN_PROGRESS, deadline_at=None))
    result = await interactor.submit_draft(
        OrderTransitionCommand(order_id=1, actor_user_id=CREATOR)
    )
    assert result.status == OrderStatus.DRAFT_REVIEW.value
    saved_order, _, events = repo.saved[0]
    assert saved_order.deadline_at is not None
    assert events[0].event_type == "order.draft_submitted"


async def test_초안_컨펌하면_작업중_복귀와_컨펌_이벤트가_저장된다():
    interactor, repo = _interactor(_order(OrderStatus.DRAFT_REVIEW))
    result = await interactor.approve_draft(
        OrderTransitionCommand(order_id=1, actor_user_id=BRAND)
    )
    assert result.status == OrderStatus.IN_PROGRESS.value
    assert result.draft_approved is True
    assert repo.saved[0][2][0].event_type == "order.draft_approved"


async def test_수정_요청은_피드백_본문이_전이와_함께_저장된다():
    # 갭 #84 — 코멘트가 같은 save_transition 호출에 실려야 원자성이 보장된다
    interactor, repo = _interactor(_order(OrderStatus.IN_REVIEW))
    result = await interactor.request_revision(
        RevisionRequestCommand(order_id=1, actor_user_id=BRAND, comment="로고가 잘렸어요 — 다시 촬영 부탁해요")
    )
    assert result.status == OrderStatus.IN_PROGRESS.value
    assert repo.revision_comments == ["로고가 잘렸어요 — 다시 촬영 부탁해요"]
    assert repo.saved[0][2][0].event_type == "order.revision_requested"
