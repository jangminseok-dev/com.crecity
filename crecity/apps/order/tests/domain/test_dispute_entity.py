from datetime import datetime, timezone

import pytest

from order.domain.entities.dispute_entity import (
    Dispute,
    DisputeResolution,
    DisputeStatus,
    InvalidDisputeStateError,
)
from order.domain.entities.ledger_entry_entity import LedgerEntryType
from order.domain.entities.order_entity import (
    InvalidOrderTransitionError,
    Order,
    OrderStatus,
)

_NOW = datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc)
BRAND, CREATOR, OPERATOR = 100, 200, 9


def _dispute(status=DisputeStatus.OPEN):
    return Dispute(
        id=1,
        order_id=42,
        raised_by_user_id=BRAND,
        reason="요구사항과 다른 결과물이 제출되었습니다.",
        status=status,
    )


def _order(status=OrderStatus.IN_REVIEW):
    return Order(
        id=42,
        package_id=10,
        package_title="릴스 1개",
        brand_user_id=BRAND,
        creator_user_id=CREATOR,
        amount_krw=300_000,
        brand_fee_percent=10,
        creator_fee_percent=10,
        requirements="60초 릴스",
        status=status,
        deadline_at=_NOW,
    )


def test_판정하면_RESOLVED로_바뀌고_판정자가_남는다():
    resolved = _dispute().resolve(DisputeResolution.REFUND, OPERATOR, _NOW)
    assert resolved.status is DisputeStatus.RESOLVED
    assert resolved.resolution is DisputeResolution.REFUND
    assert resolved.resolved_by_user_id == OPERATOR
    assert resolved.resolved_at == _NOW


def test_이미_처리된_분쟁은_다시_판정할_수_없다():
    resolved = _dispute(DisputeStatus.RESOLVED)
    with pytest.raises(InvalidDisputeStateError):
        resolved.resolve(DisputeResolution.RELEASE, OPERATOR, _NOW)


def test_환불_판정은_주문을_취소하고_브랜드에게_전액_환불한다():
    order, entries = _order().resolve_dispute_refund()
    assert order.status is OrderStatus.CANCELLED
    assert order.deadline_at is None
    assert [(e.entry_type, e.user_id, e.amount_krw) for e in entries] == [
        (LedgerEntryType.BRAND_CREDIT_REFUND, BRAND, 330_000)
    ]


def test_지급_판정은_구매_확정과_같은_기입을_만든다():
    order, entries = _order().resolve_dispute_release()
    assert order.status is OrderStatus.COMPLETED
    assert [(e.entry_type, e.user_id, e.amount_krw) for e in entries] == [
        (LedgerEntryType.CREATOR_EARNING, CREATOR, 270_000),
        (LedgerEntryType.PLATFORM_REVENUE, None, 60_000),
    ]


def test_이미_종료된_주문은_환불_지급_판정을_할_수_없다():
    completed = _order(OrderStatus.COMPLETED)
    with pytest.raises(InvalidOrderTransitionError):
        completed.resolve_dispute_refund()
    with pytest.raises(InvalidOrderTransitionError):
        completed.resolve_dispute_release()


def test_신고는_당사자만_진행_중_주문에서_할_수_있다():
    _order().ensure_can_raise_dispute(CREATOR)  # 예외 없음
    with pytest.raises(InvalidOrderTransitionError):
        _order(OrderStatus.PENDING_ACCEPT).ensure_can_raise_dispute(BRAND)
