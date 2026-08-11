from datetime import timedelta

import pytest

from hub.app.dtos.package_summary_dto import PackageSummary
from order.app.dtos.order_placement_dto import OrderPlacementCommand
from order.app.exceptions import (
    InsufficientCreditError,
    NotBrandAccountError,
    PackageNotOrderableError,
)
from order.app.use_cases.order_placement_interactor import OrderPlacementInteractor
from order.domain.entities.ledger_entry_entity import LedgerEntryType
from order.domain.entities.order_entity import OrderStatus

BRAND, CREATOR = 100, 200


class _StubPackageSummaryPort:
    def __init__(self, summary: PackageSummary | None):
        self.summary = summary

    async def get_package_summary(self, package_id):
        return self.summary if self.summary and self.summary.package_id == package_id else None


class _StubOrderRepository:
    def __init__(self, credit_ok=True):
        self.created = []  # (order, entries, events)
        self.credit_spends = []  # create에 전달된 크레딧 차감 초안
        self.credit_ok = credit_ok  # False면 잔액 부족 시뮬레이션(None 반환)

    async def create(self, order, entries, events, credit_spend=None):
        if credit_spend is not None and not self.credit_ok:
            return None
        self.created.append((order, entries, events))
        self.credit_spends.append(credit_spend)
        from dataclasses import replace

        return replace(order, id=1)

    async def find_by_id(self, order_id):
        raise NotImplementedError

    async def save_transition(self, order, entries, events):
        raise NotImplementedError

    async def list_by_participant(self, user_id):
        raise NotImplementedError

    async def find_expired(self, now, limit):
        raise NotImplementedError


_SUMMARY = PackageSummary(package_id=10, title="릴스 1개", price_krw=300000, creator_user_id=CREATOR)


def _interactor(summary=_SUMMARY, orders=None):
    return OrderPlacementInteractor(
        orders=orders if orders is not None else _StubOrderRepository(),
        packages=_StubPackageSummaryPort(summary),
        brand_fee_percent=10,
        creator_fee_percent=10,
        accept_deadline=timedelta(hours=72),
    )


def _command(package_id=10, account_type="BRAND", credit_used_krw=0):
    return OrderPlacementCommand(
        package_id=package_id,
        requirements="60초 릴스",
        brand_user_id=BRAND,
        account_type=account_type,
        credit_used_krw=credit_used_krw,
    )


async def test_주문하면_스냅샷과_72h_마감으로_수락_대기가_된다():
    orders = _StubOrderRepository()
    result = await _interactor(orders=orders).place(_command())

    assert result.status == OrderStatus.PENDING_ACCEPT.value
    assert result.amount_krw == 300000  # 패키지 가격 스냅샷
    assert result.brand_total_krw == 330000
    assert result.brand_fee_percent == 10  # 요율 스냅샷
    assert result.creator_user_id == CREATOR
    assert result.deadline_at is not None

    saved_order, saved_entries, saved_events = orders.created[0]
    assert saved_order.deadline_at is not None


async def test_주문_생성과_함께_에스크로_예치가_기록된다():
    orders = _StubOrderRepository()
    await _interactor(orders=orders).place(_command())
    _, entries, events = orders.created[0]
    assert len(entries) == 1
    assert entries[0].entry_type is LedgerEntryType.ESCROW_DEPOSIT
    assert entries[0].user_id == BRAND
    assert entries[0].amount_krw == 330000  # 수수료 포함 결제 총액
    assert events[0].event_type == "order.placed"  # Outbox 이벤트 동반


async def test_크레딧_사용분은_차감_초안으로_함께_전달된다():
    orders = _StubOrderRepository()
    await _interactor(orders=orders).place(_command(credit_used_krw=50000))
    credit_spend = orders.credit_spends[0]
    assert credit_spend is not None
    assert credit_spend.entry_type is LedgerEntryType.CREDIT_SPENT
    assert credit_spend.user_id == BRAND
    assert credit_spend.amount_krw == 50000


async def test_크레딧을_안_쓰면_차감_초안이_없다():
    orders = _StubOrderRepository()
    await _interactor(orders=orders).place(_command())
    assert orders.credit_spends[0] is None


async def test_크레딧_잔액_부족이면_InsufficientCreditError():
    orders = _StubOrderRepository(credit_ok=False)
    with pytest.raises(InsufficientCreditError):
        await _interactor(orders=orders).place(_command(credit_used_krw=999999))


async def test_크리에이터_계정이면_NotBrandAccountError():
    with pytest.raises(NotBrandAccountError):
        await _interactor().place(_command(account_type="CREATOR"))


async def test_없는_패키지면_PackageNotOrderableError():
    with pytest.raises(PackageNotOrderableError):
        await _interactor().place(_command(package_id=999))


async def test_주문_불가_패키지면_PackageNotOrderableError():
    with pytest.raises(PackageNotOrderableError):
        await _interactor(summary=None).place(_command())


# ── 커스텀 오퍼 주문 ─────────────────────────────────────────────


class _StubCustomOfferPort:
    def __init__(self, offer):
        self.offer = offer

    async def get_payable_offer(self, offer_id):
        return self.offer if self.offer and self.offer.offer_id == offer_id else None

    async def mark_paid(self, offer_id, order_id):
        raise NotImplementedError


def _offer(offer_id=5, brand_user_id=BRAND, price=450000):
    from hub.app.dtos.custom_offer_dto import CustomOfferSummary

    return CustomOfferSummary(
        offer_id=offer_id, title="맞춤 릴스 2건", price_krw=price,
        brand_user_id=brand_user_id, creator_user_id=CREATOR,
    )


def _custom_interactor(offer, orders=None):
    return OrderPlacementInteractor(
        orders=orders if orders is not None else _StubOrderRepository(),
        packages=_StubPackageSummaryPort(None),
        brand_fee_percent=10,
        creator_fee_percent=10,
        accept_deadline=timedelta(hours=72),
        offers=_StubCustomOfferPort(offer),
    )


def _custom_command(offer_id=5, brand_user_id=BRAND, account_type="BRAND"):
    from order.app.dtos.order_placement_dto import CustomOrderPlacementCommand

    return CustomOrderPlacementCommand(
        offer_id=offer_id, requirements="협의한 내용대로 진행해 주세요.",
        brand_user_id=brand_user_id, account_type=account_type,
    )


async def test_커스텀_오퍼_주문은_오퍼_스냅샷으로_생성된다():
    orders = _StubOrderRepository()
    result = await _custom_interactor(_offer(), orders).place_custom(_custom_command())
    order, entries, events = orders.created[0]
    assert order.package_id is None  # 패키지 없는 주문
    assert order.package_title == "맞춤 릴스 2건"
    assert order.amount_krw == 450000
    assert order.creator_user_id == CREATOR
    assert entries[0].amount_krw == 495000  # 가격 + 브랜드 수수료 10%
    assert result.status == OrderStatus.PENDING_ACCEPT.value


async def test_결제_불가_오퍼는_주문할_수_없다():
    with pytest.raises(PackageNotOrderableError):
        await _custom_interactor(None).place_custom(_custom_command())


async def test_오퍼_수신_브랜드가_아니면_주문할_수_없다():
    with pytest.raises(NotBrandAccountError):
        await _custom_interactor(_offer()).place_custom(_custom_command(brand_user_id=999))
