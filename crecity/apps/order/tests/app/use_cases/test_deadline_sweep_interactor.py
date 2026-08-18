from datetime import datetime, timedelta, timezone

from order.app.use_cases.deadline_sweep_interactor import DeadlineSweepInteractor
from order.domain.entities.ledger_entry_entity import LedgerEntryType
from order.domain.entities.order_entity import Order, OrderStatus

BRAND, CREATOR = 100, 200


def _order(id, status, deadline_at):
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
        status=status,
        deadline_at=deadline_at,
    )


_WARNING_THRESHOLD = timedelta(hours=12)


class _StubOrderRepository:
    def __init__(self, expired: list[Order], warning_targets: list[Order] | None = None):
        self.expired = expired
        self.warning_targets = warning_targets or []
        self.saved = []  # (order, entries)
        self.warned = []  # (order_ids, events)

    async def create(self, order, entries, events):
        raise NotImplementedError

    async def find_by_id(self, order_id):
        raise NotImplementedError

    async def save_transition(self, order, entries, events):
        self.saved.append((order, entries, events))

    async def list_by_participant(self, user_id):
        raise NotImplementedError

    async def find_expired(self, now, limit):
        return self.expired[:limit]

    async def find_deadline_warning_targets(self, now, threshold, limit):
        return self.warning_targets[:limit]

    async def record_deadline_warnings(self, order_ids, now, events):
        self.warned.append((order_ids, events))


async def test_수락_만료는_환불_검토_만료는_승인으로_전이된다():
    # 인터랙터는 실제 현재 시각으로 판정한다 — 확실히 지난 마감시각을 준다
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    repo = _StubOrderRepository(
        [
            _order(1, OrderStatus.PENDING_ACCEPT, past),
            _order(2, OrderStatus.IN_REVIEW, past),
        ]
    )
    result = await DeadlineSweepInteractor(repo, _WARNING_THRESHOLD).sweep()

    by_id = {o.order_id: o.status for o in result.outcomes}
    assert by_id[1] == OrderStatus.REFUNDED.value
    assert by_id[2] == OrderStatus.COMPLETED.value

    refund_entries = repo.saved[0][1]
    refund_events = repo.saved[0][2]
    complete_entries = repo.saved[1][1]
    assert refund_entries[0].entry_type is LedgerEntryType.BRAND_CREDIT_REFUND
    assert refund_events[0].event_type == "order.rejected"
    assert {e.entry_type for e in complete_entries} == {
        LedgerEntryType.CREATOR_EARNING,
        LedgerEntryType.PLATFORM_REVENUE,
    }


async def test_만료_대상이_없으면_아무_일도_없다():
    repo = _StubOrderRepository([])
    result = await DeadlineSweepInteractor(repo, _WARNING_THRESHOLD).sweep()
    assert result.outcomes == []
    assert repo.saved == []


async def test_마감이_임박하면_한_번_알린다():
    now = datetime.now(timezone.utc)
    소진임박 = _order(1, OrderStatus.PENDING_ACCEPT, now + timedelta(hours=5))
    repository = _StubOrderRepository([], warning_targets=[소진임박])
    result = await DeadlineSweepInteractor(repository, _WARNING_THRESHOLD).sweep()

    assert result.warned_order_ids == [1]
    order_ids, events = repository.warned[0]
    assert order_ids == [1]
    assert events[0].event_type == "order.deadline_soon"
    # 수락 대기는 크리에이터가 움직여야 한다
    assert events[0].payload["recipient_user_id"] == CREATOR
    # 알림 문구가 갈리는 값 — payload에 담기지 않으면 "검토해 주세요"로 잘못 나간다
    assert events[0].payload["order_status"] == OrderStatus.PENDING_ACCEPT.value


async def test_검토_마감은_브랜드에게_알린다():
    now = datetime.now(timezone.utc)
    검토임박 = _order(2, OrderStatus.IN_REVIEW, now + timedelta(hours=3))
    repository = _StubOrderRepository([], warning_targets=[검토임박])
    await DeadlineSweepInteractor(repository, _WARNING_THRESHOLD).sweep()
    _, events = repository.warned[0]
    assert events[0].payload["recipient_user_id"] == BRAND
    assert events[0].payload["order_status"] == OrderStatus.IN_REVIEW.value


async def test_이미_알린_주문은_다시_알리지_않는다():
    now = datetime.now(timezone.utc)
    from dataclasses import replace

    이미알림 = replace(
        _order(3, OrderStatus.PENDING_ACCEPT, now + timedelta(hours=5)),
        deadline_warned_at=now - timedelta(hours=1),
    )
    repository = _StubOrderRepository([], warning_targets=[이미알림])
    result = await DeadlineSweepInteractor(repository, _WARNING_THRESHOLD).sweep()
    assert result.warned_order_ids == []
    assert repository.warned == []


async def test_마감이_아직_멀면_알리지_않는다():
    now = datetime.now(timezone.utc)
    여유 = _order(4, OrderStatus.PENDING_ACCEPT, now + timedelta(hours=40))
    repository = _StubOrderRepository([], warning_targets=[여유])
    result = await DeadlineSweepInteractor(repository, _WARNING_THRESHOLD).sweep()
    assert result.warned_order_ids == []


async def test_제출하면_임박_표식이_비워진다():
    # 검토 마감에도 한 번 더 알려야 한다
    from dataclasses import replace

    now = datetime.now(timezone.utc)
    진행중 = replace(
        _order(5, OrderStatus.IN_PROGRESS, None), deadline_warned_at=now - timedelta(hours=2)
    )
    제출됨 = 진행중.submit(
        actor_user_id=CREATOR, now=now, review_deadline=timedelta(hours=72), deliverable_count=1
    )
    assert 제출됨.deadline_warned_at is None


async def test_초안_검토_만료는_자동_컨펌이고_컨펌_알림이_실린다():
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    repo = _StubOrderRepository([_order(1, OrderStatus.DRAFT_REVIEW, past)])
    result = await DeadlineSweepInteractor(repo, _WARNING_THRESHOLD).sweep()
    order, entries, events = repo.saved[0]
    assert order.status is OrderStatus.IN_PROGRESS
    assert order.draft_approved is True
    assert entries == []  # 돈이 움직이지 않는다
    assert events[0].event_type == "order.draft_approved"
    assert result.outcomes[0].status == OrderStatus.IN_PROGRESS.value
