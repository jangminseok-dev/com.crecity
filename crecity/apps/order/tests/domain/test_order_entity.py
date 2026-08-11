from datetime import datetime, timedelta, timezone

import pytest

from order.domain.entities.ledger_entry_entity import LedgerEntryType
from order.domain.entities.order_entity import (
    InvalidOrderTransitionError,
    NotOrderActorError,
    Order,
    OrderStatus,
)

_NOW = datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc)
_72H = timedelta(hours=72)
BRAND, CREATOR = 100, 200


def _order(status=OrderStatus.PENDING_ACCEPT, deadline_at=_NOW + _72H, amount_krw=300000):
    return Order(
        id=1,
        package_id=10,
        package_title="릴스 1개",
        brand_user_id=BRAND,
        creator_user_id=CREATOR,
        amount_krw=amount_krw,
        brand_fee_percent=10,
        creator_fee_percent=10,
        requirements="신제품 소개 60초 릴스",
        status=status,
        deadline_at=deadline_at,
    )


# ── 수수료 계산 ────────────────────────────────────────────────────────────


def test_수수료는_주문_스냅샷_요율로_정수_계산된다():
    order = _order(amount_krw=300000)
    assert order.brand_fee_krw() == 30000
    assert order.brand_total_krw() == 330000  # 브랜드 결제 총액(에스크로 예치액)
    assert order.creator_payout_krw() == 270000  # 크리에이터 적립액
    assert order.platform_revenue_krw() == 60000


def test_수수료_계산은_내림이다():
    order = _order(amount_krw=99999)
    assert order.brand_fee_krw() == 9999  # 9999.9 → 내림
    assert order.creator_payout_krw() == 90000


# ── 정상 전이 흐름 ─────────────────────────────────────────────────────────


def test_수락하면_작업중이_되고_마감이_사라진다():
    accepted = _order().accept(CREATOR)
    assert accepted.status is OrderStatus.IN_PROGRESS
    assert accepted.deadline_at is None


def test_거절하면_환불되고_브랜드_크레딧이_적립된다():
    refunded, entries = _order().reject(CREATOR)
    assert refunded.status is OrderStatus.REFUNDED
    assert len(entries) == 1
    assert entries[0].entry_type is LedgerEntryType.BRAND_CREDIT_REFUND
    assert entries[0].user_id == BRAND
    assert entries[0].amount_krw == 330000  # 수수료 포함 전액 환불


def test_제출하면_검토중이_되고_72h_마감이_걸린다():
    submitted = _order(OrderStatus.IN_PROGRESS, deadline_at=None).submit(CREATOR, _NOW, _72H, 1)
    assert submitted.status is OrderStatus.IN_REVIEW
    assert submitted.deadline_at == _NOW + _72H


def test_납품물이_없으면_제출할_수_없다():
    with pytest.raises(InvalidOrderTransitionError):
        _order(OrderStatus.IN_PROGRESS, deadline_at=None).submit(CREATOR, _NOW, _72H, 0)


def test_수정_요청하면_다시_작업중이_된다():
    revising = _order(OrderStatus.IN_REVIEW).request_revision(BRAND)
    assert revising.status is OrderStatus.IN_PROGRESS
    assert revising.deadline_at is None


def test_수정_요청은_스냅샷된_횟수까지만_가능하다():
    order = _order(OrderStatus.IN_PROGRESS, deadline_at=None)  # revision_limit 기본 2
    for _ in range(2):
        order = order.submit(CREATOR, _NOW, _72H, 1)
        order = order.request_revision(BRAND)
    assert order.revisions_used == 2 and order.revisions_left() == 0
    with pytest.raises(InvalidOrderTransitionError):
        order.submit(CREATOR, _NOW, _72H, 1).request_revision(BRAND)


def test_승인하면_완료되고_적립과_수수료가_기록된다():
    completed, entries = _order(OrderStatus.IN_REVIEW).approve(BRAND)
    assert completed.status is OrderStatus.COMPLETED
    by_type = {e.entry_type: e for e in entries}
    earning = by_type[LedgerEntryType.CREATOR_EARNING]
    revenue = by_type[LedgerEntryType.PLATFORM_REVENUE]
    assert earning.user_id == CREATOR and earning.amount_krw == 270000
    assert revenue.user_id is None and revenue.amount_krw == 60000


# ── 권한(행위자) 검증 ──────────────────────────────────────────────────────


def test_브랜드가_수락하면_NotOrderActorError():
    with pytest.raises(NotOrderActorError):
        _order().accept(BRAND)


def test_크리에이터가_승인하면_NotOrderActorError():
    with pytest.raises(NotOrderActorError):
        _order(OrderStatus.IN_REVIEW).approve(CREATOR)


def test_제3자는_아무_전이도_못_한다():
    with pytest.raises(NotOrderActorError):
        _order().accept(999)
    with pytest.raises(NotOrderActorError):
        _order(OrderStatus.IN_REVIEW).request_revision(999)


# ── 잘못된 상태에서의 전이 ─────────────────────────────────────────────────


def test_작업중_주문을_다시_수락하면_InvalidOrderTransitionError():
    with pytest.raises(InvalidOrderTransitionError):
        _order(OrderStatus.IN_PROGRESS, deadline_at=None).accept(CREATOR)


def test_완료된_주문은_어떤_전이도_거부한다():
    done = _order(OrderStatus.COMPLETED, deadline_at=None)
    with pytest.raises(InvalidOrderTransitionError):
        done.reject(CREATOR)
    with pytest.raises(InvalidOrderTransitionError):
        done.submit(CREATOR, _NOW, _72H, 1)
    with pytest.raises(InvalidOrderTransitionError):
        done.approve(BRAND)


def test_검토중이_아니면_승인할_수_없다():
    with pytest.raises(InvalidOrderTransitionError):
        _order(OrderStatus.IN_PROGRESS, deadline_at=None).approve(BRAND)


# ── 양측 합의 취소 ─────────────────────────────────────────────────────────


def test_취소_요청은_당사자_누구나_할_수_있고_상태는_유지된다():
    for actor in (BRAND, CREATOR):
        requested = _order(OrderStatus.IN_PROGRESS, deadline_at=None).request_cancellation(actor)
        assert requested.cancel_requested_by == actor
        assert requested.status is OrderStatus.IN_PROGRESS


def test_제3자는_취소_요청을_못_한다():
    with pytest.raises(NotOrderActorError):
        _order(OrderStatus.IN_PROGRESS, deadline_at=None).request_cancellation(999)


def test_작업_전이나_종결_후에는_취소_요청_불가():
    for status in (OrderStatus.PENDING_ACCEPT, OrderStatus.COMPLETED, OrderStatus.REFUNDED):
        with pytest.raises(InvalidOrderTransitionError):
            _order(status, deadline_at=None).request_cancellation(BRAND)


def test_취소_요청_중복은_거부된다():
    requested = _order(OrderStatus.IN_PROGRESS, deadline_at=None).request_cancellation(BRAND)
    with pytest.raises(InvalidOrderTransitionError):
        requested.request_cancellation(CREATOR)


def test_상대가_동의하면_취소되고_브랜드에게_전액_환불된다():
    requested = _order(OrderStatus.IN_PROGRESS, deadline_at=None).request_cancellation(BRAND)
    cancelled, entries = requested.consent_cancellation(CREATOR)
    assert cancelled.status is OrderStatus.CANCELLED
    assert cancelled.deadline_at is None
    assert entries[0].entry_type is LedgerEntryType.BRAND_CREDIT_REFUND
    assert entries[0].user_id == BRAND
    assert entries[0].amount_krw == 330000  # 수수료 포함 전액


def test_요청자_본인은_동의할_수_없다():
    requested = _order(OrderStatus.IN_PROGRESS, deadline_at=None).request_cancellation(BRAND)
    with pytest.raises(NotOrderActorError):
        requested.consent_cancellation(BRAND)


def test_대기_요청이_없으면_동의도_거부도_불가():
    order = _order(OrderStatus.IN_PROGRESS, deadline_at=None)
    with pytest.raises(InvalidOrderTransitionError):
        order.consent_cancellation(CREATOR)
    with pytest.raises(InvalidOrderTransitionError):
        order.decline_cancellation(CREATOR)


def test_상대가_거부하면_요청이_해제되고_주문은_계속된다():
    requested = _order(OrderStatus.IN_REVIEW).request_cancellation(CREATOR)
    declined = requested.decline_cancellation(BRAND)
    assert declined.cancel_requested_by is None
    assert declined.status is OrderStatus.IN_REVIEW


# ── 만료(주기 스캔) ────────────────────────────────────────────────────────


def test_수락_대기_만료는_자동_환불이다():
    expired = _order(deadline_at=_NOW - timedelta(minutes=1)).expire(_NOW)
    assert expired is not None
    order, entries = expired
    assert order.status is OrderStatus.REFUNDED
    assert entries[0].entry_type is LedgerEntryType.BRAND_CREDIT_REFUND


def test_검토_만료는_자동_승인이다():
    expired = _order(OrderStatus.IN_REVIEW, deadline_at=_NOW - timedelta(minutes=1)).expire(_NOW)
    assert expired is not None
    order, entries = expired
    assert order.status is OrderStatus.COMPLETED
    assert {e.entry_type for e in entries} == {
        LedgerEntryType.CREATOR_EARNING,
        LedgerEntryType.PLATFORM_REVENUE,
    }


def test_마감_전이면_expire는_None이다():
    assert _order(deadline_at=_NOW + timedelta(hours=1)).expire(_NOW) is None


def test_마감이_없는_상태는_expire_대상이_아니다():
    assert _order(OrderStatus.IN_PROGRESS, deadline_at=None).expire(_NOW) is None
