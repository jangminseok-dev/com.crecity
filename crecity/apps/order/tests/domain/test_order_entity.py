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


# ── 진행 중 금액 변경 (갭 #31) ────────────────────────────────────────────


def test_추가_결제가_반영되면_금액이_늘고_증가분만_예치된다():
    order = _order(OrderStatus.IN_PROGRESS, deadline_at=None)  # 300,000 / 예치 330,000
    increased, entries = order.apply_adjustment(100000)
    assert increased.amount_krw == 400000
    assert increased.brand_total_krw() == 440000
    assert entries[0].entry_type is LedgerEntryType.ESCROW_DEPOSIT
    assert entries[0].amount_krw == 110000  # 늘어난 만큼만(수수료 포함)


def test_종결된_주문은_금액_변경이_불가하다():
    with pytest.raises(InvalidOrderTransitionError):
        _order(OrderStatus.COMPLETED, deadline_at=None).apply_adjustment(100000)


def test_추가_금액이_0이하면_거부된다():
    with pytest.raises(InvalidOrderTransitionError):
        _order(OrderStatus.IN_PROGRESS, deadline_at=None).apply_adjustment(0)


def test_금액_변경_요청은_진행_중_크리에이터만():
    _order(OrderStatus.IN_PROGRESS, deadline_at=None).ensure_can_request_adjustment(CREATOR)
    with pytest.raises(NotOrderActorError):
        _order(OrderStatus.IN_PROGRESS, deadline_at=None).ensure_can_request_adjustment(BRAND)
    with pytest.raises(InvalidOrderTransitionError):
        _order(OrderStatus.COMPLETED, deadline_at=None).ensure_can_request_adjustment(CREATOR)


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


def test_수락_대기_만료는_자동_환불이고_페널티_표식이_남는다():
    expired = _order(deadline_at=_NOW - timedelta(minutes=1)).expire(_NOW)
    assert expired is not None
    order, entries = expired
    assert order.status is OrderStatus.REFUNDED
    assert order.accept_expired is True  # 랭킹 페널티 대상(§3.8)
    assert entries[0].entry_type is LedgerEntryType.BRAND_CREDIT_REFUND


def test_크리에이터_거절_환불은_페널티_표식이_없다():
    refunded, _entries = _order().reject(CREATOR)
    assert refunded.status is OrderStatus.REFUNDED
    assert refunded.accept_expired is False  # 무응답이 아니라 명시적 거절


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


# ── 초안 검토 (게시 전 컨펌 — 갭 #85) ─────────────────────────────────────


def test_초안을_제출하면_초안_검토가_되고_72h_마감이_걸린다():
    order = _order(status=OrderStatus.IN_PROGRESS, deadline_at=None)
    drafted = order.submit_draft(CREATOR, _NOW, _72H, deliverable_count=1)
    assert drafted.status is OrderStatus.DRAFT_REVIEW
    assert drafted.deadline_at == _NOW + _72H
    assert drafted.draft_approved is False


def test_납품물이_없으면_초안을_제출할_수_없다():
    order = _order(status=OrderStatus.IN_PROGRESS, deadline_at=None)
    with pytest.raises(InvalidOrderTransitionError):
        order.submit_draft(CREATOR, _NOW, _72H, deliverable_count=0)


def test_초안_제출은_크리에이터만():
    order = _order(status=OrderStatus.IN_PROGRESS, deadline_at=None)
    with pytest.raises(NotOrderActorError):
        order.submit_draft(BRAND, _NOW, _72H, deliverable_count=1)


def test_초안을_컨펌하면_작업중으로_돌아가고_표식이_남는다():
    order = _order(status=OrderStatus.DRAFT_REVIEW)
    approved = order.approve_draft(BRAND)
    assert approved.status is OrderStatus.IN_PROGRESS
    assert approved.deadline_at is None
    assert approved.draft_approved is True


def test_초안_컨펌은_브랜드만():
    order = _order(status=OrderStatus.DRAFT_REVIEW)
    with pytest.raises(NotOrderActorError):
        order.approve_draft(CREATOR)


def test_컨펌된_초안은_다시_제출할_수_없다():
    order = _order(status=OrderStatus.DRAFT_REVIEW).approve_draft(BRAND)
    with pytest.raises(InvalidOrderTransitionError):
        order.submit_draft(CREATOR, _NOW, _72H, deliverable_count=1)


def test_초안_검토에서도_수정_요청이_되고_같은_한도를_쓴다():
    order = _order(status=OrderStatus.DRAFT_REVIEW)
    revised = order.request_revision(BRAND)
    assert revised.status is OrderStatus.IN_PROGRESS
    assert revised.revisions_used == 1


def test_초안_검토_만료는_자동_컨펌이고_돈이_움직이지_않는다():
    order = _order(status=OrderStatus.DRAFT_REVIEW, deadline_at=_NOW - timedelta(hours=1))
    outcome = order.expire(_NOW)
    assert outcome is not None
    expired, entries = outcome
    assert expired.status is OrderStatus.IN_PROGRESS
    assert expired.draft_approved is True
    assert entries == []


def test_초안_검토_중에도_취소_요청과_분쟁이_가능하다():
    order = _order(status=OrderStatus.DRAFT_REVIEW)
    assert order.request_cancellation(BRAND).cancel_requested_by == BRAND
    order.ensure_can_raise_dispute(CREATOR)  # 예외 없으면 통과
