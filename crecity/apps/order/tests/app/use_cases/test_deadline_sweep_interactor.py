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


class _StubOrderRepository:
    def __init__(self, expired: list[Order]):
        self.expired = expired
        self.saved = []  # (order, entries)

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


async def test_수락_만료는_환불_검토_만료는_승인으로_전이된다():
    # 인터랙터는 실제 현재 시각으로 판정한다 — 확실히 지난 마감시각을 준다
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    repo = _StubOrderRepository(
        [
            _order(1, OrderStatus.PENDING_ACCEPT, past),
            _order(2, OrderStatus.IN_REVIEW, past),
        ]
    )
    result = await DeadlineSweepInteractor(repo).sweep()

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
    result = await DeadlineSweepInteractor(repo).sweep()
    assert result.outcomes == []
    assert repo.saved == []
